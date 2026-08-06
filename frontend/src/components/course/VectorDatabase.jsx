import { useState } from "react";

import {
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Box,
  Chip,
  Stack,
} from "@mui/material";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PsychologyIcon from "@mui/icons-material/Psychology";

import api from "../../api/api";

function VectorDatabase({ courseId }) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [message, setMessage] = useState("");

  async function generateVectorDB() {
    try {
      setLoading(true);
      setMessage("");

      const response = await api.post(
        `/generate-vector-db/${courseId}`
      );

      setSuccess(true);
      setMessage(response.data);

    } catch (error) {

      console.log(error);

      setSuccess(false);
      setMessage("Vector Database generation failed.");

    } finally {

      setLoading(false);

    }
  }

  return (
    <Paper
      elevation={3}
      sx={{
        p: 4,
        borderRadius: 4,
        mb: 4,
      }}
    >
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography
          variant="h5"
          fontWeight="bold"
        >
          ⚡ AI Knowledge Base
        </Typography>

        <Chip
          color={
            success ? "success" : "warning"
          }
          icon={
            success ? (
              <CheckCircleIcon />
            ) : (
              <PsychologyIcon />
            )
          }
          label={
            success
              ? "AI Ready"
              : "Not Generated"
          }
        />
      </Stack>

      <Typography
        color="text.secondary"
        mb={4}
      >
        Generate embeddings from uploaded
        course material to enable
        Retrieval-Augmented Generation (RAG)
        inside the AI Tutor.
      </Typography>

      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
        }}
      >
        <Button
          size="large"
          variant="contained"
          startIcon={<AutoAwesomeIcon />}
          disabled={loading}
          onClick={generateVectorDB}
          sx={{
            px: 5,
            py: 1.5,
          }}
        >
          {loading ? (
            <CircularProgress
              size={24}
              color="inherit"
            />
          ) : (
            "Generate Vector Database"
          )}
        </Button>
      </Box>

      {message && (
        <Alert
          sx={{ mt: 4 }}
          severity={
            success
              ? "success"
              : "error"
          }
        >
          {message}
        </Alert>
      )}
    </Paper>
  );
}

export default VectorDatabase;