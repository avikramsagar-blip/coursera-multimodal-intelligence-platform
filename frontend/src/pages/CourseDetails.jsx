import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api/api";

function CourseDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [videos, setVideos] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [vectorMessage, setVectorMessage] = useState("");

  useEffect(() => {
    fetchVideos();
  }, []);

  async function fetchVideos() {
    try {
      const response = await api.get(`/videos/${id}`);
      setVideos(response.data);
    } catch (error) {
      console.log(error);
    }
  }

  async function uploadPDF() {
    if (!selectedFile) {
      alert("Please select a PDF");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await api.post(
        `/upload-course-material?course_id=${id}`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log(response.data);
      setUploadMessage("✅ PDF Uploaded Successfully");
    } catch (error) {
      console.log(error);
      alert("PDF Upload Failed");
    }
  }

  async function generateVectorDB() {
    try {
      const response = await api.post(`/generate-vector-db/${id}`);

      console.log(response.data);

      setVectorMessage("✅ Vector Database Generated Successfully");
    } catch (error) {
      console.log(error);
      alert("Vector DB Generation Failed");
    }
  }

  return (
    <div
      style={{
        width: "900px",
        margin: "30px auto",
        fontFamily: "Arial",
      }}
    >
      <h1>📚 Course Details</h1>

      <hr />

      <h2>📄 Upload Course Material</h2>

      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setSelectedFile(e.target.files[0])}
      />

      <br />
      <br />

      <button
        onClick={uploadPDF}
        style={{
          padding: "10px 20px",
          cursor: "pointer",
        }}
      >
        Upload PDF
      </button>

      <p>{uploadMessage}</p>

      <hr />

      <h2>🧠 Generate Vector Database</h2>

      <button
        onClick={generateVectorDB}
        style={{
          padding: "10px 20px",
          cursor: "pointer",
        }}
      >
        Generate Vector DB
      </button>

      <p>{vectorMessage}</p>

      <hr />

      <h2>🎥 Course Videos</h2>

      {videos.length === 0 ? (
        <p>No Videos Found</p>
      ) : (
        videos.map((video) => (
          <div
            key={video.video_id}
            style={{
              border: "1px solid gray",
              padding: "20px",
              borderRadius: "10px",
              marginBottom: "20px",
            }}
          >
            <h3>{video.title}</h3>

            <p>{video.description}</p>

            <p>
              <b>Duration:</b> {video.duration} sec
            </p>

            <a
              href={video.video_url}
              target="_blank"
              rel="noreferrer"
            >
              ▶ Watch Video
            </a>
          </div>
        ))
      )}

      <hr />

      <button
        onClick={() => navigate(`/course/${id}/ai`)}
        style={{
          padding: "12px 25px",
          cursor: "pointer",
          fontSize: "16px",
        }}
      >
        🤖 Ask AI Tutor
      </button>
    </div>
  );
}

export default CourseDetails;