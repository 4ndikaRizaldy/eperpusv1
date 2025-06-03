import streamlit as st
import os
import json
from PIL import Image
import base64
import time
import plotly.express as px

ADMIN_PASSWORD = "admin123"
# Fungsi untuk memuat data buku
def load_books():
    if not os.path.exists("books.json"):
        return []

    with open("books.json", "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []

# Simpan Data Buku
def save_books(books):
    with open("books.json","w") as f:
        json.dump(books, f, indent=4)

# Header utama
def render_header():
    st.markdown("""
        <h1 style='text-align: center; color: navy;'>📚 E-Perpustakaan</h1>
        <p style='text-align: center;'>Temukan dan baca koleksi buku digital favoritmu langsung dari browser!</p>
        <hr>
    """, unsafe_allow_html=True)
    
def render_stats():
    st.subheader("📊 Statistik Koleksi Buku")
    
    # Load buku
    books = load_books()

    # Hitung jumlah buku per kategori
    category_count = {}
    for book in books:
        category = book.get('category', 'Lainnya')
        category_count[category] = category_count.get(category, 0) + 1

    # Ubah data untuk visualisasi
    category_labels = list(category_count.keys())
    category_values = list(category_count.values())

    # Pilih jenis chart (Bar Chart atau Pie Chart)
    chart_type = st.radio("Pilih Jenis Grafik", ("Bar Chart", "Pie Chart"))

    if chart_type == "Bar Chart":
        # Bar Chart
        fig = px.bar(
            x=category_labels, y=category_values,
            labels={'x': 'Kategori', 'y': 'Jumlah Buku'},
            title="Jumlah Buku per Kategori"
        )
        st.plotly_chart(fig)

    elif chart_type == "Pie Chart":
        # Pie Chart
        fig = px.pie(
            names=category_labels, values=category_values,
            title="Distribusi Buku per Kategori"
        )
        st.plotly_chart(fig)

# Tampilan daftar buku
def render_book_list(books, keyword=""):
    st.subheader("📖 Koleksi Buku Tersedia")

    if keyword:
        books = [
            book for book in books
            if keyword.lower() in book["title"].lower() or keyword.lower() in book["author"].lower()
        ]

    if not books:
        st.info("Buku tidak ditemukan.")
        return

    cols = st.columns(3)
    for idx, book in enumerate(books):
        with cols[idx % 3]:
            try:
                cover_path = os.path.join("covers", book["cover"])
                image = Image.open(cover_path)
                st.image(image, use_container_width=True)
            except:
                st.warning("Cover tidak ditemukan.")
            
            st.markdown(f"**{book['title']}**")
            st.markdown(f"_oleh {book['author']}_")
            st.caption(f"📂 {book.get('category', 'Lainnya')}")


            if st.button(f"Baca", key=f"read_{idx}"):
                st.session_state.selected_book = book
                st.rerun()

# Fungsi utama homepage
def homepage():
    render_header()
    books = load_books()
    render_most_popular_books(books)

    # Input pencarian & kategori
    cols = st.columns([2, 1])
    with cols[0]:
        search = st.text_input("🔎 Cari buku (judul/penulis):")
    with cols[1]:
        categories = ["Semua"] + sorted(list({b.get("category", "Lainnya") for b in books}))
        selected_category = st.selectbox("📂 Kategori", categories)

    # Filter berdasarkan kategori
    if selected_category != "Semua":
        books = [b for b in books if b.get("category") == selected_category]

    # 🔽 Tambahan: Pilihan urutan
    sort_option = st.selectbox(
        "↕️ Urutkan berdasarkan",
        ["Judul (A-Z)", "Judul (Z-A)", "Penulis", "Populer (Paling Banyak Dibaca)", "Kategori"]
    )

    # 🔽 Lakukan pengurutan berdasarkan pilihan
    if sort_option == "Judul (A-Z)":
        books = sorted(books, key=lambda x: x["title"].lower())
    elif sort_option == "Judul (Z-A)":
        books = sorted(books, key=lambda x: x["title"].lower(), reverse=True)
    elif sort_option == "Penulis":
        books = sorted(books, key=lambda x: x["author"].lower())
    elif sort_option == "Populer (Paling Banyak Dibaca)":
        books = sorted(books, key=lambda x: x.get("view_count", 0), reverse=True)
    elif sort_option == "Kategori":
        books = sorted(books, key=lambda x: x.get("category", "").lower())

    render_book_list(books, keyword=search)

    

def show_book_reader(book):
    st.title(book['title'])
    st.markdown(f"_oleh {book['author']}_")
    pdf_path = os.path.join("books", book["file"])

    # Hitung view hanya sekali
    if not st.session_state.get("view_tracked", False):
        book["view_count"] = book.get("view_count", 0) + 1

        # Load buku, update ke list global dan simpan ke file
        with open("books.json", "r") as f:
            books = json.load(f)

        for b in books:
            if b["title"] == book["title"] and b["author"] == book["author"]:
                b["view_count"] = book["view_count"]
                break

        save_books(books)
        st.session_state.view_tracked = True  # Flag agar tidak dihitung lagi

    # Tampilkan PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error("File buku tidak ditemukan.")

    # Tombol kembali
    if st.button("⬅ Kembali ke Beranda"):
        st.session_state.selected_book = None
        st.session_state.view_tracked = False  # Reset flag
        st.rerun()


# Tambah Buku – hanya untuk admin
def add_book_page():
    if not st.session_state.get("admin_logged_in", False):
        st.subheader("🔒 Admin Login")
        password = st.text_input("Masukkan password admin:", type="password")
        if st.button("Login"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("Login berhasil!")
            else:
                st.error("Password salah.")
        return

    st.subheader("📥 Tambah Buku Baru")

    title = st.text_input("Judul Buku")
    author = st.text_input("Penulis")
    pdf_file = st.file_uploader("Unggah File PDF", type=["pdf"])
    cover_file = st.file_uploader("Unggah Gambar Cover", type=["jpg", "jpeg", "png"])
    category = st.selectbox("Kategori", ["Fiksi", "Non-Fiksi", "Sains", "Teknologi", "Biografi", "Sejarah", "Religi", "Lainnya"])
    
    if st.button("Simpan Buku"):
        if not (title and author and pdf_file and cover_file):
            st.error("Harap lengkapi semua kolom.")
            return

        filename_base = title.replace(" ", "_").lower()
        pdf_path = os.path.join("books", f"{filename_base}.pdf")
        cover_path = os.path.join("covers", f"{filename_base}.jpg")


        # Simpan file
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())
        with open(cover_path, "wb") as f:
            f.write(cover_file.read())

        # Simpan ke JSON
        books = load_books()
        books.append({
            "title": title,
            "author": author,
            "file": f"{filename_base}.pdf",
            "cover": f"{filename_base}.jpg",
            "category": category
        })

        save_books(books)

        st.success("Buku berhasil ditambahkan!")

def kelola_buku_page():
    if not st.session_state.get("admin_logged_in", False):
        st.error("Akses hanya untuk admin.")
        return

    st.subheader("🛠 Kelola Buku")

    books = load_books()
    for idx, book in enumerate(books):
        with st.expander(f"📖 {book['title']} - {book['author']}"):
            st.caption(f"Kategori: {book.get('category', 'Lainnya')}")

            # Edit Form
            title = st.text_input("Judul", value=book["title"], key=f"title_{idx}")
            author = st.text_input("Penulis", value=book["author"], key=f"author_{idx}")
            category = st.selectbox("Kategori", [
                "Fiksi", "Non-Fiksi", "Sains", "Teknologi", "Biografi", "Sejarah", "Religi", "Lainnya"
            ], index=["Fiksi", "Non-Fiksi", "Sains", "Teknologi", "Biografi", "Sejarah", "Religi", "Lainnya"].index(book.get("category", "Lainnya")), key=f"cat_{idx}")

            new_cover = st.file_uploader("Ganti Cover (opsional)", type=["jpg", "jpeg", "png"], key=f"cover_{idx}")
            new_file = st.file_uploader("Ganti PDF (opsional)", type=["pdf"], key=f"pdf_{idx}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Simpan Perubahan", key=f"edit_{idx}"):
                    filename_base = title.replace(" ", "_").lower()

                    # Update cover jika ada upload baru
                    if new_cover:
                        new_cover_filename = f"{filename_base}.jpg"
                        cover_path = os.path.join("covers", new_cover_filename)
                        with open(cover_path, "wb") as f:
                            f.write(new_cover.read())
                        book["cover"] = new_cover_filename

                    # Update file PDF jika ada upload baru
                    if new_file:
                        new_pdf_filename = f"{filename_base}.pdf"
                        pdf_path = os.path.join("books", new_pdf_filename)
                        with open(pdf_path, "wb") as f:
                            f.write(new_file.read())
                        book["file"] = new_pdf_filename

                    # Update data dasar
                    book["title"] = title
                    book["author"] = author
                    book["category"] = category

                    # Simpan kembali ke JSON
                    books[idx] = book  # Pastikan data di books diperbarui
                    save_books(books)
                    st.success("✅ Perubahan berhasil disimpan.")
                    time.sleep(1)
                    st.rerun()
                with col2:
                    with st.container():
                        confirm_delete = st.checkbox(f"Konfirmasi hapus buku ini", key=f"confirm_{idx}")
                        if st.button("🗑 Hapus Buku", key=f"delete_{idx}"):
                            if confirm_delete:
                                try:
                                    if os.path.exists(os.path.join("books", book["file"])):
                                        os.remove(os.path.join("books", book["file"]))

                                    if os.path.exists(os.path.join("covers", book["cover"])):
                                        os.remove(os.path.join("covers", book["cover"]))
                                except Exception as e:
                                    st.warning(f"⚠️ Gagal hapus file: {e}")

                                books.pop(idx)
                                save_books(books)
                                st.success("✅ Buku berhasil dihapus.")
                                st.rerun()
                            else:
                                st.warning("⚠️ Harap konfirmasi dulu sebelum menghapus buku.")


def render_most_popular_books(books, top_n=5):
    st.subheader("🔥 Buku Paling Populer")
    sorted_books = sorted(books, key=lambda b: b.get("view_count", 0), reverse=True)[:top_n]

    for idx, book in enumerate(sorted_books):
        st.markdown(f"**{idx+1}. {book['title']}** oleh {book['author']}")
        st.caption(f"📊 Dilihat {book.get('view_count', 0)} kali")

        
# Fungsi utama
def main():
    st.set_page_config(page_title="E-Perpustakaan", layout="wide")

    # Inisialisasi sesi
    if "selected_book" not in st.session_state:
        st.session_state.selected_book = None
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    # 📖 Load buku
    books = load_books()
    
    # Sidebar
    with st.sidebar:
        st.title("📚 Menu")
        page = st.radio("Navigasi", ["Beranda","Popular Book","Tambah Buku","Kelola Buku", "Statistik Buku"])
        if st.session_state.admin_logged_in:
            if st.button("Logout Admin"):
                st.session_state.admin_logged_in = False
                st.success("Berhasil logout.")

    # Routing halaman
    if page == "Beranda":
        if st.session_state.selected_book:
            show_book_reader(st.session_state.selected_book)
        else:
            homepage()
    elif page == "Popular Book":
        render_most_popular_books(books, top_n=5)
    elif page == "Statistik Buku":
        render_stats()
    elif page == "Tambah Buku":
        add_book_page()
    elif page == "Kelola Buku":
        kelola_buku_page()

# Jalankan aplikasi
if __name__ == "__main__":
    main()