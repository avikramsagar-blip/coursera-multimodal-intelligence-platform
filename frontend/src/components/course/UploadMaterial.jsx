import { useState } from "react";
import { useParams } from "react-router-dom";

import {
  Paper,
  Typography,
  Button,
  Alert,
  List,
  ListItem,
  ListItemText,
  Box,
  CircularProgress,
} from "@mui/material";

import CloudUploadIcon from "@mui/icons-material/CloudUpload";

import api from "../../api/api";

function UploadMaterial({ onUploadSuccess }) {

  const { id } = useParams();

  const courseId = Number(id);

  const [files, setFiles] = useState([]);

  const [loading, setLoading] = useState(false);

  const [message, setMessage] = useState("");

  function handleChange(e) {
    const selected = Array.from(e.target.files);
    console.log("[handleChange] files selected:", selected.length, selected.map(f => f.name));
    setFiles(selected);
  }

  async function handleUpload() {

    if (files.length === 0) {
      setMessage("Please select PDF files.");
      return;
    }

    console.log("[handleUpload] files.length:", files.length, files.map(f => f.name));

    const formData = new FormData();
    formData.append("course_id", courseId);
    files.forEach((file) => formData.append("files", file));

    console.log("[handleUpload] FormData entries:");
    for (const [key, val] of formData.entries()) {
      console.log(" ", key, val instanceof File ? val.name : val);
    }

    try {
      setLoading(true);
      setMessage("");

      await api.post("/upload-course-material", formData);
      await api.post(`/generate-vector-db/${courseId}`);

      setMessage("Files uploaded and AI knowledge base updated successfully");
      setFiles([]);
      if (onUploadSuccess) onUploadSuccess();

    } catch (error) {
      setMessage(error.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }

  }

  return (

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
        mb={2}
      >

        Upload Course Materials

      </Typography>

      <Button
        component="label"
        variant="outlined"
        startIcon={<CloudUploadIcon />}
        fullWidth
      >

        Select PDFs

        <input
          hidden
          multiple
          type="file"
          accept=".pdf"
          onChange={handleChange}
        />

      </Button>

      {

        files.length > 0 && (

          <Box mt={3}>

            <Typography
              fontWeight="bold"
              mb={1}
            >

              Selected Files

            </Typography>

            <List>

              {

                files.map((file, index) => (

                  <ListItem key={index}>

                    <ListItemText
                      primary={file.name}
                    />

                  </ListItem>

                ))

              }

            </List>

          </Box>

        )

      }

      <Button
        variant="contained"
        fullWidth
        sx={{ mt: 3 }}
        disabled={loading}
        onClick={handleUpload}
      >

        {

          loading ?

          <CircularProgress
            size={22}
            color="inherit"
          />

          :

          "Upload Materials"

        }

      </Button>

      {

        message && (

          <Alert
            severity={
              message.includes("success")
              ? "success"
              : "error"
            }
            sx={{ mt: 3 }}
          >

            {message}

          </Alert>

        )

      }

    </Paper>

  );

}

export default UploadMaterial;