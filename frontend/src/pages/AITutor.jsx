import { useState } from "react";
import { useParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import api from "../api/api";

function AITutor() {

  const { id } = useParams();

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function askAI() {

    if (!question.trim()) {
      alert("Please enter a question");
      return;
    }

    try {

      setLoading(true);

      const response = await api.post(
        "/course-rag-chat",
        {
          course_id: Number(id),
          question: question,
        }
      );

      setAnswer(response.data.answer);

    } catch (error) {

      console.log(error);

      alert(
        error.response?.data?.detail ||
        "Failed to get AI response"
      );

    } finally {

      setLoading(false);

    }
  }

  return (
    <>
      <Navbar />

      <div className="container mt-5">

        <div className="card shadow">

          <div className="card-body">

            <h2 className="mb-4">
              🤖 AI Tutor
            </h2>

            <textarea
              className="form-control"
              rows="5"
              placeholder="Ask anything about this course..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />

            <button
              className="btn btn-primary mt-3"
              onClick={askAI}
              disabled={loading}
            >

              {loading ? "Thinking..." : "Ask AI"}

            </button>

            {answer && (

              <div
                className="card mt-4 border-success"
              >

                <div className="card-header bg-success text-white">

                  AI Response

                </div>

                <div className="card-body">

                  <p
                    style={{
                      whiteSpace: "pre-wrap",
                      fontSize: "16px"
                    }}
                  >

                    {answer}

                  </p>

                </div>

              </div>

            )}

          </div>

        </div>

      </div>
    </>
  );
}

export default AITutor;