import { useState } from "react";

import {
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Box,
} from "@mui/material";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";

import api from "../../api/api";

function VectorDatabase({ courseId }) {
  const [loading, setLoading] = useState(false);

  const [status, setStatus] = useState("");

  async function generateVectorDB() {
    try {
      setLoading(true);
      setStatus("");

      const response = await api.post(
        `/generate-vector-db/${courseId}`
      );

      setStatus(response.data);

    } catch (error) {

      console.log(error);

      setStatus("Failed to generate Vector Database.");

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
      <Typography
        variant="h5"
        fontWeight="bold"
        mb={3}
      >
        ⚡ AI Vector Database
      </Typography>

      <Typography
        color="text.secondary"
        mb={3}
      >
        Generate embeddings from uploaded course material
        so the AI Tutor can answer questions using RAG.
      </Typography>

      <Button
        variant="contained"
        size="large"
        startIcon={<AutoAwesomeIcon />}
        disabled={loading}
        onClick={generateVectorDB}
        sx={{
          borderRadius: 3,
          textTransform: "none",
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

      {status && (
        <Box mt={3}>
          <Alert
            severity={
              status.toLowerCase().includes("fail")
                ? "error"
                : "success"
            }
          >
            {status}
          </Alert>
        </Box>
      )}
    </Paper>
  );
}

export default VectorDatabase;