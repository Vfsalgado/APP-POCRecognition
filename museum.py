import boto3
import streamlit as st
from PIL import Image
import io

def compare_with_s3_images(uploaded_image, bucket_name, similarity_threshold=70):
    rekognition_client = boto3.client('rekognition', region_name='us-east-2')
    s3_client = boto3.client('s3', region_name='us-east-2')

    # Obter a lista de imagens do bucket
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if 'Contents' not in response:
        return []

    matching_images = []

    # Converter imagem carregada para bytes
    image_bytes = io.BytesIO()
    uploaded_image.save(image_bytes, format=uploaded_image.format)
    image_bytes.seek(0)

    for obj in response['Contents']:
        key = obj['Key']
        
        # Pular se não for imagem
        if not key.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        # Comparar a imagem com as do bucket S3
        try:
            compare_response = rekognition_client.compare_faces(
                SourceImage={"Bytes": image_bytes.getvalue()},
                TargetImage={"S3Object": {"Bucket": bucket_name, "Name": key}},
                SimilarityThreshold=similarity_threshold
            )

            for face_match in compare_response['FaceMatches']:
                similarity = face_match['Similarity']
                if similarity >= similarity_threshold:
                    # Adicionar o nome e a similaridade da imagem correspondente
                    matching_images.append((key, similarity))

        except Exception as e:
            print(f"Erro ao comparar com {key}: {e}")

    return matching_images

def load_image_from_s3(bucket_name, key):
    """Carregar imagem do bucket S3 como objeto PIL."""
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    image_bytes = response['Body'].read()
    image = Image.open(io.BytesIO(image_bytes))
    return image



# Função para verificar o login
def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

# Função para processar o login
def login(username, password):
    if username == "feluma" and password == "feluma123":
        st.session_state.logged_in = True
        st.rerun()  # Redireciona imediatamente após o login bem-sucedido
    else:
        st.error("Usuário ou senha incorretos.")
        

if not st.session_state.logged_in:
    st.title("Login")  # Altera o título para "Login"
    username = st.text_input("Usuário:")
    password = st.text_input("Senha:", type="password")
    
    if st.button("Entrar"):
        login(username, password)
    
    # Verifica se o usuário está logado
    check_login()
        
else:       
    # Configuração inicial da página
    st.set_page_config(layout="wide", page_title="Image Comparison APP")
    
    # Botão de logout
    logout_clicked = st.button("Sair")
    if logout_clicked:
        st.session_state.logged_in = False
        st.rerun() 

    # Título principal
    st.write("## Museu de Imagens Feluma")

    # Configuração da barra lateral
    st.sidebar.write("## Upload de imagem :gear:")

    # Nome do bucket S3
    bucket_name = "fotos-museu"

    # Upload da imagem
    file1 = st.sidebar.file_uploader("Upload da Imagem", type=["png", "jpg", "jpeg"])

    if file1:
        # Abrindo a imagem com PIL
        img1 = Image.open(file1)

        # Dividindo a página para exibir informações e imagem
        col1, col2 = st.columns([1, 2])

        with col1:
            # Exibição do nome do arquivo
            st.write(f"### Foto: {file1.name}")

        with col2:
            # Exibição da imagem
            st.image(img1, caption="Imagem Enviada", width=500)

        # Realizar comparação com imagens no bucket S3
        st.write("### Comparando com imagens no bucket S3...")
        matching_images = compare_with_s3_images(img1, bucket_name)

        if matching_images:
            st.write("### Imagens Correspondentes:")
            for image_name, similarity in matching_images:
                # Carregar a imagem do S3
                image = load_image_from_s3(bucket_name, image_name)
                # Exibir a imagem e a similaridade
                st.image(image, caption=f"{image_name} (Similaridade: {similarity:.2f}%)", width=300)
        else:
            st.write("Nenhuma imagem correspondente encontrada.")
    else:
        # Mensagem caso nenhuma imagem seja carregada
        st.write("Por favor, selecione uma imagem válida para exibir e comparar.")




