import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Box,
  Typography,
  Grid,
  Paper,
  Divider,
  Button,
} from "@mui/material";

import api from "../api/api";
import Layout from "../components/Layout";

import DashboardHeader from "../components/dashboard/DashboardHeader";
import SearchBar from "../components/dashboard/SearchBar";
import StatsSection from "../components/dashboard/StatsSection";
import CourseCard from "../components/dashboard/CourseCard";

function Dashboard() {

  const navigate = useNavigate();

  const [courses, setCourses] = useState([]);

  const [search, setSearch] = useState("");

  // Show create course button when logged in (token present)
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchCourses();
  }, []);

  async function fetchCourses() {

    try {

      const response = await api.get("/courses");

      console.log("COURSES RESPONSE", response.data, "TYPE", typeof response.data, "IS_ARRAY", Array.isArray(response.data));

      const data = Array.isArray(response.data)
        ? response.data
        : (response.data?.courses ?? response.data?.data ?? []);

      setCourses(data);

    } catch (error) {

      console.log(error);

    }

  }

  const filteredCourses = courses.filter((course) =>
    course.title
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (

    <Layout>

      <Box
        sx={{
          p: 4,
        }}
      >

        <DashboardHeader />

        {token && (
          <Box sx={{ mb: 2, textAlign: 'right' }}>
            <Button variant="contained" onClick={() => navigate('/courses/new')}>
              Create Course
            </Button>
          </Box>
        )}

        <SearchBar
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
        />

        <StatsSection
          totalCourses={courses.length}
        />

        <Divider sx={{ my: 4 }} />

        <Typography
          variant="h5"
          fontWeight="bold"
          mb={3}
        >
          📚 Featured Courses
        </Typography>

        {filteredCourses.length === 0 ? (

          <Paper
            sx={{
              p: 5,
              textAlign: "center",
              borderRadius: 4,
            }}
          >

            <Typography variant="h6">

              No Courses Found

            </Typography>

          </Paper>

        ) : (

          <Grid
            container
            spacing={3}
          >

            {filteredCourses.map((course) => (

              <Grid
                key={course.course_id}
                size={{
                  xs: 12,
                  md: 6,
                  lg: 6,
                }}
              >

                <CourseCard

                  course={course}

                  onOpen={() =>
                    navigate(
                      `/course/${course.course_id}`
                    )
                  }

                />

              </Grid>

            ))}

          </Grid>

        )}

      </Box>

    </Layout>

  );

}

export default Dashboard;