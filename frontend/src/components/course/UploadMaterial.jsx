import { useState } from "react";

import {
  Paper,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
  Stack,
} from "@mui/material";

import UploadFileIcon from "@mui/icons-material/UploadFile";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";

import api from "../../api/api";

function UploadMaterial({ courseId, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleUpload() {
    if (!file) {
      setMessage("Please select a PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("");

      await api.post(
        `/upload-course-material?course_id=${courseId}`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setMessage("Material uploaded successfully.");

      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error) {
      console.log(error);
      setMessage("Upload failed.");
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
        📄 Upload Course Material
      </Typography>

      <Box
        sx={{
          border: "2px dashed #4F46E5",
          borderRadius: 4,
          p: 5,
          textAlign: "center",
          bgcolor: "#F8FAFC",
        }}
      >
        <CloudUploadIcon
          color="primary"
          sx={{
            fontSize: 70,
            mb: 2,
          }}
        />

        <Typography
          variant="h6"
          mb={1}
        >
          Drag & Drop PDF Here
        </Typography>

        <Typography
          color="text.secondary"
          mb={3}
        >
          or choose a file from your computer
        </Typography>

        <Button
          component="label"
          variant="outlined"
          startIcon={<UploadFileIcon />}
        >
          Choose PDF

          <input
            hidden
            type="file"
            accept=".pdf"
            onChange={(e) =>
              setFile(e.target.files[0])
            }
          />
        </Button>

        {file && (
          <Typography
            mt={3}
            color="primary"
            fontWeight="bold"
          >
            {file.name}
          </Typography>
        )}
      </Box>

      <Stack
        direction="row"
        justifyContent="flex-end"
        mt={3}
      >
        <Button
          variant="contained"
          size="large"
          disabled={loading}
          onClick={handleUpload}
        >
          {loading ? (
            <CircularProgress
              size={24}
              color="inherit"
            />
          ) : (
            "Upload Material"
          )}
        </Button>
      </Stack>

      {message && (
        <Alert
          sx={{ mt: 3 }}
          severity={
            message.includes("success")
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

export default UploadMaterial;