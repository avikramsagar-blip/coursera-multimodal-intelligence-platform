import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";

import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
} from "@mui/material";

import SchoolIcon from "@mui/icons-material/School";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";

import Layout from "../components/Layout";
import UploadMaterial from "../components/course/UploadMaterial";
import VideoSection from "../components/course/VideoSection";

import api from "../api/api";


function CourseDetails() {

  // ---------------------------------
  // Router
  // ---------------------------------

  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();


  // ---------------------------------
  // Evidence Navigation State
  // ---------------------------------

  const targetVideoId =
    location.state?.targetVideoId ?? null;

  const seekTime =
    location.state?.seekTime ?? null;


  // ---------------------------------
  // State
  // ---------------------------------

  const [course, setCourse] = useState(null);

  const [videos, setVideos] = useState([]);

  const [materials, setMaterials] = useState([]);

  const [loading, setLoading] = useState(true);

  const [generating, setGenerating] = useState(false);

  const [error, setError] = useState("");

  const [success, setSuccess] = useState("");


  // ---------------------------------
  // Load Data
  // ---------------------------------

  useEffect(() => {

    loadData();

  }, [id]);


  // ---------------------------------
  // Load Course + Videos + Materials
  // ---------------------------------

  async function loadData() {

    try {

      setLoading(true);

      setError("");

      const [
        courseRes,
        videoRes,
        materialRes,
      ] = await Promise.all([

        api.get(`/courses/${id}`),

        api.get(`/videos/${id}`),

        api.get(`/course-materials/${id}`),

      ]);


      setCourse(courseRes.data);

      setVideos(videoRes.data);

      setMaterials(materialRes.data);


    } catch (error) {

      console.log(error);

      setError(
        error.response?.data?.detail ||
        "Unable to load course details."
      );

    } finally {

      setLoading(false);

    }

  }


  // ---------------------------------
  // Delete Material
  // ---------------------------------

  async function deleteMaterial(materialId) {

    const ok = window.confirm(
      "Delete this PDF?"
    );

    if (!ok) return;


    try {

      setError("");

      setSuccess("");


      await api.delete(
        `/course-material/${materialId}`
      );


      await loadData();


      setSuccess(
        "Course material deleted successfully."
      );


    } catch (error) {

      console.log(error);


      setError(
        error.response?.data?.detail ||
        "Delete failed."
      );

    }

  }


  // ---------------------------------
  // Generate Vector DB
  // ---------------------------------

  async function generateVectorDB() {

    if (materials.length === 0) {

      setError(
        "Please upload at least one PDF before generating the AI knowledge base."
      );

      return;

    }


    try {

      setGenerating(true);

      setError("");

      setSuccess("");


      const response = await api.post(
        `/generate-vector-db/${id}`
      );


      setSuccess(
        response.data?.message ||
        "AI knowledge base generated successfully."
      );


    } catch (error) {

      console.log(
        "Vector DB generation error:",
        error
      );


      setError(
        error.response?.data?.detail ||
        "Failed to generate AI knowledge base."
      );


    } finally {

      setGenerating(false);

    }

  }


  // ---------------------------------
  // Loading
  // ---------------------------------

  if (loading) {

    return (

      <Layout>

        <Box
          display="flex"
          justifyContent="center"
          mt={10}
        >

          <CircularProgress />

        </Box>

      </Layout>

    );

  }


  // ---------------------------------
  // UI
  // ---------------------------------

  return (

    <Layout>

      <Box
        sx={{
          maxWidth: 1100,
          mx: "auto",
          py: 4,
          px: 2,
        }}
      >


        {/* -------------------------------- */}
        {/* Error */}
        {/* -------------------------------- */}

        {error && (

          <Alert
            severity="error"
            sx={{ mb: 3 }}
            onClose={() =>
              setError("")
            }
          >

            {error}

          </Alert>

        )}


        {/* -------------------------------- */}
        {/* Success */}
        {/* -------------------------------- */}

        {success && (

          <Alert
            severity="success"
            sx={{ mb: 3 }}
            onClose={() =>
              setSuccess("")
            }
          >

            {success}

          </Alert>

        )}


        {/* -------------------------------- */}
        {/* Course Header */}
        {/* -------------------------------- */}

        <Paper
          elevation={3}
          sx={{
            p: 3,
            borderRadius: 3,
            mb: 4,
          }}
        >

          <Stack
            direction="row"
            spacing={2}
            alignItems="center"
          >

            <SchoolIcon
              color="primary"
              sx={{
                fontSize: 40,
              }}
            />

            <Box>

              <Typography
                variant="h4"
                fontWeight="bold"
              >

                {course?.title}

              </Typography>


              {course?.description && (

                <Typography
                  color="text.secondary"
                  sx={{ mt: 1 }}
                >

                  {course.description}

                </Typography>

              )}

            </Box>

          </Stack>

        </Paper>


        {/* -------------------------------- */}
        {/* Course Materials */}
        {/* -------------------------------- */}

        <Paper
          elevation={3}
          sx={{
            p: 3,
            borderRadius: 3,
          }}
        >

          <Typography
            variant="h6"
            fontWeight="bold"
            gutterBottom
          >

            Course Materials

          </Typography>


          <Divider
            sx={{ mb: 2 }}
          />


          {/* Upload PDF */}

          <UploadMaterial
            courseId={id}
            onUploadSuccess={loadData}
          />


          <Divider
            sx={{ my: 3 }}
          />


          {/* Existing Materials */}

          {materials.length === 0 ? (

            <Typography
              color="text.secondary"
            >

              No course materials uploaded.

            </Typography>

          ) : (

            <List>

              {materials.map(
                (material) => (

                  <ListItem
                    key={
                      material.material_id
                    }
                    secondaryAction={

                      <Button
                        variant="outlined"
                        color="error"
                        size="small"
                        onClick={() =>
                          deleteMaterial(
                            material.material_id
                          )
                        }
                      >

                        Delete

                      </Button>

                    }
                  >

                    <PictureAsPdfIcon
                      color="error"
                      sx={{
                        mr: 2,
                      }}
                    />


                    <ListItemText
                      primary={
                        material.file_name
                      }
                    />

                  </ListItem>

                )
              )}

            </List>

          )}

        </Paper>


        {/* -------------------------------- */}
        {/* AI Knowledge Base */}
        {/* -------------------------------- */}

        <Paper
          elevation={3}
          sx={{
            p: 3,
            borderRadius: 3,
            mt: 4,
            backgroundColor: "#F8FAFC",
          }}
        >

          <Stack
            direction="row"
            spacing={2}
            alignItems="center"
            mb={1}
          >

            <AutoAwesomeIcon
              color="primary"
            />

            <Typography
              variant="h6"
              fontWeight="bold"
            >

              AI Knowledge Base

            </Typography>

          </Stack>


          <Typography
            color="text.secondary"
            sx={{ mb: 2 }}
          >

            Generate or rebuild the AI
            knowledge base from the uploaded
            course PDFs and video transcripts.
            The AI Tutor will use this material
            to answer course-related questions.

          </Typography>


          <Button
            variant="contained"
            startIcon={

              generating ? (

                <CircularProgress
                  size={20}
                  color="inherit"
                />

              ) : (

                <AutoAwesomeIcon />

              )

            }
            disabled={generating}
            onClick={
              generateVectorDB
            }
          >

            {generating
              ? "Generating..."
              : "Generate AI Knowledge Base"}

          </Button>


          {materials.length === 0 && (

            <Typography
              variant="caption"
              display="block"
              color="text.secondary"
              sx={{ mt: 1 }}
            >

              Upload a PDF first.

            </Typography>

          )}

        </Paper>


        {/* -------------------------------- */}
        {/* Course Videos */}
        {/* -------------------------------- */}

        <Paper
          elevation={3}
          sx={{
            p: 3,
            borderRadius: 3,
            mt: 4,
          }}
        >

          <Typography
            variant="h6"
            fontWeight="bold"
            gutterBottom
          >

            Course Videos

          </Typography>


          <Divider
            sx={{ mb: 3 }}
          />


          {videos.length === 0 ? (

            <Typography
              color="text.secondary"
            >

              No videos available.

            </Typography>

          ) : (

            <VideoSection
              videos={videos}
              targetVideoId={
                targetVideoId
              }
              seekTime={
                seekTime
              }
              onRefresh={
                loadData
              }
            />

          )}

        </Paper>


        {/* -------------------------------- */}
        {/* Simple Video List */}
        {/* -------------------------------- */}

        {videos.length > 0 && (

          <Paper
            elevation={2}
            sx={{
              p: 3,
              borderRadius: 3,
              mt: 3,
            }}
          >

            <Typography
              variant="subtitle1"
              fontWeight="bold"
              gutterBottom
            >

              All Course Videos

            </Typography>


            <List>

              {videos.map(
                (video) => (

                  <ListItem
                    key={
                      video.video_id
                    }
                  >

                    <PlayArrowIcon
                      color="primary"
                      sx={{
                        mr: 2,
                      }}
                    />


                    <ListItemText
                      primary={
                        video.title
                      }
                      secondary={
                        video.duration
                      }
                    />

                  </ListItem>

                )
              )}

            </List>

          </Paper>

        )}


        {/* -------------------------------- */}
        {/* AI Tutor */}
        {/* -------------------------------- */}

        <Button
          fullWidth
          variant="contained"
          size="large"
          startIcon={
            <SmartToyIcon />
          }
          sx={{
            mt: 4,
            py: 1.5,
          }}
          onClick={() =>
            navigate("/ai-tutor")
          }
        >

          Open AI Tutor

        </Button>


      </Box>

    </Layout>

  );

}


export default CourseDetails;