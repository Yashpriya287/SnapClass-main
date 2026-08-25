import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding,identify_speaker
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject,update_student_voice_embedding
import time

from src.components.dailog_enroll import enroll_dialog
from src.components.subject_card import subject_card

def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {student_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            del st.session_state.student_data 
            st.rerun()


    st.space()

    c1, c2 =st.columns([3,1])
    with c1:
        st.header('Your Enrolled Subjects')
    with c2:
        if st.button('Enroll in Subject', type='primary', width='stretch'):
            enroll_dialog()


    st.divider()


    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log['subject_id']

        if sid not in stats_map:
            stats_map[sid] = {"total":0, "attended": 0}

        stats_map[sid]['total'] +=1

        if log.get('is_present'):
            stats_map[sid]['attended'] += 1


    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']


        stats = stats_map.get(sid,{"total":0, "attended": 0} )
        def unenroll_button():
                if st.button("Unenroll from tihs course", type='tertiary', width='stretch', icon=':material/delete_forever:'):
                    unenroll_student_to_subject(student_id, sid)
                    st.toast(f'Unenrolled from {sub['name']} successfully!')
                    st.rerun()

        with cols[i % 2]:

            subject_card(
                name = sub['name'],
                code =sub['subject_code'],
                section = sub['section'],
                stats = [
                    ('📅', 'Total', stats['total']),
                    ('✅', 'Attended', stats['attended']),
                ],
                footer_callback=unenroll_button
            )
    footer_dashboard()




def get_voice_candidates():

    students = get_all_students()

    candidates = {}

    for student in students:

        voice_embedding = student.get("voice_embedding")

        if voice_embedding:
            candidates[student["student_id"]] = voice_embedding

    return candidates




def student_screen():


    style_background_dashboard()
    style_base_layout()

    if "show_voice_registration" not in st.session_state:
       st.session_state.show_voice_registration = False

    if "voice_registration_embedding" not in st.session_state:
       st.session_state.voice_registration_embedding = None

    if "show_registration" not in st.session_state:
       st.session_state.show_registration = False   


    if "student_data" in st.session_state:
        student_dashboard()
        return
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header(
            "Login using FaceID or VoiceID",
            text_alignment="center"
        )

    

    st.divider()
    
    #face_col, voice_col = st.columns(2)
    #with face_col:
    st.header("📷 FaceID")

    photo_source = st.camera_input(
        "Position your face in the center"
    )

    if photo_source:

        img = np.array(Image.open(photo_source))

        with st.spinner("AI is scanning.."):

            detected, all_ids, num_faces = predict_attendance(img)

        if num_faces == 0:
            st.warning("Face not found!")

        elif num_faces > 1:
            st.warning("Multiple faces found!")

        else:

            # Face recognized
            if detected:

                student_id = list(detected.keys())[0]

                all_students = get_all_students()

                student = next(
                    (
                        s for s in all_students
                        if s["student_id"] == student_id
                    ),
                    None
                )

                # Valid student found
                if student:

                    st.session_state.is_logged_in = True
                    st.session_state.user_role = "student"
                    st.session_state.student_data = student

                    st.toast(
                        f"Welcome Back {student['name']}"
                    )

                    time.sleep(1)
                    st.rerun()

                # Face detected but student doesn't exist
                else:

                    st.warning(
                        "Face detected but no student account was found."
                    )

                    st.session_state.show_registration = True
                    st.session_state.registration_photo = photo_source

            # Face not recognized
            else:

                st.warning(
                    "Face not recognized. Please register as a new student."
                )

                st.session_state.show_registration = True
                st.session_state.registration_photo = photo_source

    #with voice_col:

    st.header("🎙️ VoiceID")

    audio_data = st.audio_input(
        "Record a short phrase"
    )

    if audio_data:

        with st.spinner("Analyzing your voice..."):

            new_embedding = get_voice_embedding(
                audio_data.read()
            )

            candidates = get_voice_candidates()

            student_id, score = identify_speaker(
                new_embedding,
                candidates,
                threshold=0.65
            )

        if student_id:

            all_students = get_all_students()

            student = next(
                (
                    s for s in all_students
                    if s["student_id"] == student_id
                ),
                None
            )

            if student:

                st.success(
                    f"Voice recognized! Welcome {student['name']}"
                )

                st.session_state.is_logged_in = True
                st.session_state.user_role = "student"
                st.session_state.student_data = student

                time.sleep(1)
                st.rerun()

        else:

            st.warning(
                "Voice not registered."
            )

            st.session_state.voice_registration_embedding = new_embedding
            st.session_state.show_voice_registration = True




    if st.session_state.get("show_voice_registration"):

        with st.container(border=True):

            st.header("🎙️ Register VoiceID")

            st.info(
                "Your voice is not registered. "
                "Let's verify your FaceID and link this voice "
                "to your existing student account."
            )

            st.subheader("Step 1 — Verify your FaceID")

            verify_photo = st.camera_input(
                "Position your face in the center",
                key="voice_registration_camera"
            )

            if verify_photo:

                img = np.array(
                    Image.open(verify_photo)
                )

                with st.spinner(
                    "Verifying your identity..."
                ):

                    detected, _, num_faces = predict_attendance(
                        img
                    )

                if num_faces == 0:

                    st.warning("Face not found.")

                elif num_faces > 1:

                    st.warning(
                        "Multiple faces found. "
                        "Please make sure only you are visible."
                    )

                elif detected:

                    student_id = list(
                        detected.keys()
                    )[0]

                    all_students = get_all_students()

                    student = next(
                        (
                            s for s in all_students
                            if s["student_id"] == student_id
                        ),
                        None
                    )

                    if student:

                        voice_embedding = st.session_state.get(
                            "voice_registration_embedding"
                        )

                        if voice_embedding:

                            response = update_student_voice_embedding(
                                student_id,
                                voice_embedding
                            )

                            try:
                                update_student_voice_embedding(
                                    student_id,
                                    voice_embedding
                                )

                                st.success("VoiceID registered successfully!")

                                st.session_state.is_logged_in = True
                                st.session_state.user_role = "student"
                                st.session_state.student_data = student

                                st.session_state.show_voice_registration = False
                                st.session_state.voice_registration_embedding = None

                                time.sleep(1)
                                st.rerun()

                            except Exception as e:
                                st.error(f"Voice registration failed: {e}")

                else:

                    st.error(
                        "Face verification failed. "
                        "This voice cannot be linked to an account."
                    )
                        
    if st.session_state.show_registration:
        with st.container(border=True):
            st.header('Register new Profile')
            new_name = st.text_input("Enter your name", placeholder='E.g. Hamza Rizvi')

            st.subheader('Optional : Voice Enrollment')
            st.info("Enroll your for voice only attendance")


            audio_data = None

            try:
                audio_data = st.audio_input('Record a short phrase like I am present, My name is Akash.')
            except Exception:
                st.error('Audio Data failed!')

            if st.button('Create Account', type='primary'):
                if new_name:
                    with st.spinner('Creating profile..'):
                        img = np.array(Image.open(photo_source))
                        encodings= get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()

                            voice_emb = None
                            if audio_data:
                                voice_emb = get_voice_embedding(audio_data.read())

                            response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)

                            if response_data:
                                train_classifier()
                                st.session_state.show_registration=False
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]
                                st.toast(f'Profile Created! Hi {new_name}!')
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error('Couldnt capture your facial features for registration')

                else:
                    st.warning('Please enter your name!')


        
    footer_dashboard()