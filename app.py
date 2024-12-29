from pathlib import Path
import tempfile
import zipfile
from datetime import datetime
import streamlit as st
from pathways_task_reminder.student_reporter import StudentReporter
from pathways_task_reminder.utils.version import get_version

# Streamlit App
version = get_version()
st.title(f"Learner Progress Report (v{version})")

uploaded_file = st.file_uploader(
    "Upload your Pathways Student Summary PDF", type=["pdf"]
)
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        pdf_file_path = Path(temp_file.name)

    image_paths_by_name = StudentReporter.create_images_from_pdf(pdf_file_path)

    if not image_paths_by_name:
        st.error("No tables found in the uploaded PDF.")
    else:
        st.success(f"Found {len(image_paths_by_name)} students with data in the PDF!")

        # Create a zip file with timestamped name
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        zip_base_name = f"{timestamp}-all-student-reports"
        zip_filename = f"{zip_base_name}.zip"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
            with zipfile.ZipFile(temp_zip.name, "w") as zipf:
                for name, image_path in image_paths_by_name.items():
                    # Add files under a directory named after the zip file (without .zip)
                    arcname = f"{zip_base_name}/{name.replace(' ', '_')}.png"
                    zipf.write(
                        str(image_path),
                        arcname=arcname,  # Files inside the zip are nested under the directory
                    )
            zip_path = temp_zip.name

        # Provide download button for the zip file
        with open(zip_path, "rb") as zip_file:
            st.download_button(
                label="Download All Report Images as ZIP",
                data=zip_file,
                file_name=zip_filename,
                mime="application/zip",
            )
        st.divider()

        st.text(
            "HINT: If on phone can press on an image and then share to texting application. "
            "If on computer, can drag and drop images directly into texting applications. "
        )
        for name, image_path in image_paths_by_name.items():
            st.divider()
            message= "Hi " + name.split(" ")[0]
            name_output = name + "\n" + message
            st.image(str(image_path), caption=name_output, use_container_width=False)

            # with open(image_path, "rb") as img_file:
            #     image_bytes = img_file.read()
            #     st.download_button(
            #         label=f"Download {name}'s report individually",
            #         data=image_bytes,
            #         file_name=f"{name.replace(' ', '_')}.png",
            #         mime="image/png",
            #     )

            st.text("")
