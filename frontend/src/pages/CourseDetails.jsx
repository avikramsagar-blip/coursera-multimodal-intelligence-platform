import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  Box,
  Button,
  CircularProgress,
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
          mt={8}
        >

          <CircularProgress />

        </Box>

      </Layout>

    );

  }

  return (

    <Layout>

      <Box p={4}>

        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/dashboard")}
          sx={{ mb: 3 }}
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

        <VideoSection videos={videos} />

        <UploadMaterial
          courseId={id}
        />

        <VectorDatabase
          courseId={id}
        />

      </Box>

    </Layout>

  );

}

export default CourseDetails;