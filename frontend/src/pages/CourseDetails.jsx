import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  Box,
  Button,
  CircularProgress,
  Grid,
} from "@mui/material";

import ArrowBackIcon from "@mui/icons-material/ArrowBack";

import api from "../api/api";
import Layout from "../components/Layout";

import CourseBanner from "../components/course/CourseBanner";
import VideoSection from "../components/course/VideoSection";
import UploadMaterial from "../components/course/UploadMaterial";
import VectorDatabase from "../components/course/VectorDatabase";

function CourseDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCourse();
    fetchVideos();
  }, []);

  async function fetchCourse() {
    try {
      const response = await api.get(`/courses/${id}`);
      setCourse(response.data);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  }

  async function fetchVideos() {
    try {
      const response = await api.get(`/videos/${id}`);
      setVideos(response.data);
    } catch (error) {
      console.log(error);
    }
  }

  if (loading) {
    return (
      <Layout>
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="70vh"
        >
          <CircularProgress size={60} />
        </Box>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box sx={{ p: 4 }}>

        <Button
          startIcon={<ArrowBackIcon />}
          variant="outlined"
          sx={{ mb: 3 }}
          onClick={() => navigate("/dashboard")}
        >
          Back to Dashboard
        </Button>

        {course && (
          <CourseBanner
            course={course}
            onAITutor={() =>
              navigate(`/course/${id}/ai`)
            }
          />
        )}

        <Grid container spacing={3}>

          <Grid size={{ xs: 12, md: 8 }}>
            <VideoSection videos={videos} />
            <UploadMaterial courseId={id} />
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <VectorDatabase courseId={id} />
          </Grid>

        </Grid>

      </Box>
    </Layout>
  );
}

export default CourseDetails;