import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";


function Dashboard() {
  const navigate = useNavigate();

  const [courses, setCourses] = useState([]);

  useEffect(() => {
    fetchCourses();
  }, []);

  async function fetchCourses() {
    try {
      const response = await api.get("/courses");
      setCourses(response.data);
    } catch (error) {
      console.log(error);
      alert("Failed to load courses");
    }
  }

return (
  <Layout>

    <div className="container mt-4">

      <h2 className="mb-4 text-center">
        📚 Available Courses
      </h2>

      <div className="row">

        {courses.length === 0 ? (

          <div className="text-center">
            <h4>No Courses Available</h4>
          </div>

        ) : (

          courses.map((course) => (

            <div
              className="col-md-4 mb-4"
              key={course.course_id}
            >

              <div className="card shadow h-100">

                <div className="card-body">

                  <h4>{course.title}</h4>

                  <p>{course.description}</p>

                  <p>
                    <strong>Category:</strong> {course.category}
                  </p>

                  <p>
                    <strong>Difficulty:</strong> {course.difficulty}
                  </p>

                  <p>
                    <strong>Price:</strong> ₹{course.price}
                  </p>

                </div>

                <div className="card-footer bg-white border-0">

                  <button
                    className="btn btn-primary w-100"
                    onClick={() =>
                      navigate(`/course/${course.course_id}`)
                    }
                  >
                    Open Course
                  </button>

                </div>

              </div>

            </div>

          ))

        )}

      </div>

    </div>

  </Layout>
)};