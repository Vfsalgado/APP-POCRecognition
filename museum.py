import boto3
import streamlit as st
from PIL import Image
import io

# Function to process login
def login(username, password):
    try:
        # Check credentials
        if username == "feluma" and password == "feluma123":
            # Explicitly set logged_in to True
            st.session_state.logged_in = True
            # Force a rerun to refresh the page state
            st.experimental_rerun()
        else:
            # Clear any previous login attempts
            st.session_state.login_error = "Usuário ou senha incorretos."
            # Display error message
            st.error(st.session_state.login_error)
    except Exception as e:
        # Catch and log any unexpected errors
        st.error(f"Erro durante o login: {e}")
        # Optional: log the error for debugging
        print(f"Login error: {e}")

def compare_with_s3_images(uploaded_image, bucket_name, similarity_threshold=70):
    rekognition_client = boto3.client('rekognition', region_name='us-east-2')
    s3_client = boto3.client('s3', region_name='us-east-2')

    # Get list of images from the bucket
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if 'Contents' not in response:
        return []

    matching_images = []

    # Convert uploaded image to bytes
    image_bytes = io.BytesIO()
    uploaded_image.save(image_bytes, format=uploaded_image.format)
    image_bytes.seek(0)

    for obj in response['Contents']:
        key = obj['Key']
        
        # Skip if not an image
        if not key.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        # Compare image with S3 bucket images
        try:
            compare_response = rekognition_client.compare_faces(
                SourceImage={"Bytes": image_bytes.getvalue()},
                TargetImage={"S3Object": {"Bucket": bucket_name, "Name": key}},
                SimilarityThreshold=similarity_threshold
            )

            for face_match in compare_response['FaceMatches']:
                similarity = face_match['Similarity']
                if similarity >= similarity_threshold:
                    # Add matching image name and similarity
                    matching_images.append((key, similarity))

        except Exception as e:
            print(f"Erro ao comparar com {key}: {e}")

    return matching_images

def load_image_from_s3(bucket_name, key):
    """Load image from S3 bucket as PIL object."""
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    image_bytes = response['Body'].read()
    image = Image.open(io.BytesIO(image_bytes))
    return image

def main():
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Clear any previous login errors
    if 'login_error' in st.session_state:
        del st.session_state.login_error

    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Usuário:")
        password = st.text_input("Senha:", type="password")
        
        if st.button("Entrar"):
            login(username, password)
        
        # Display any previous login error
        if 'login_error' in st.session_state:
            st.error(st.session_state.login_error)
    
    else:       
        # Initial page configuration
        st.set_page_config(layout="wide", page_title="Image Comparison APP")
        
        # Logout button
        logout_clicked = st.button("Sair")
        if logout_clicked:
            st.session_state.logged_in = False
            st.experimental_rerun() 

        # Main title
        st.write("## Museu de Imagens Feluma")

        # Sidebar configuration
        st.sidebar.write("## Upload de imagem :gear:")

        # S3 bucket name
        bucket_name = "fotos-museu"

        # Image upload
        file1 = st.sidebar.file_uploader("Upload da Imagem", type=["png", "jpg", "jpeg"])

        if file1:
            # Open image with PIL
            img1 = Image.open(file1)

            # Split page to display information and image
            col1, col2 = st.columns([1, 2])

            with col1:
                # Display filename
                st.write(f"### Foto: {file1.name}")

            with col2:
                # Display image
                st.image(img1, caption="Imagem Enviada", width=500)

            # Compare with images in S3 bucket
            st.write("### Comparando com imagens no bucket S3...")
            matching_images = compare_with_s3_images(img1, bucket_name)

            if matching_images:
                st.write("### Imagens Correspondentes:")
                for image_name, similarity in matching_images:
                    # Load image from S3
                    image = load_image_from_s3(bucket_name, image_name)
                    # Display image and similarity
                    st.image(image, caption=f"{image_name} (Similaridade: {similarity:.2f}%)", width=300)
            else:
                st.write("Nenhuma imagem correspondente encontrada.")
        else:
            # Message if no image is uploaded
            st.write("Por favor, selecione uma imagem válida para exibir e comparar.")

# Run the main function
if __name__ == "__main__":
    main()