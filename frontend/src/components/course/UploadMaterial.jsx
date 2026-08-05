import { useState } from "react";

import {
  Paper,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
} from "@mui/material";

import UploadFileIcon from "@mui/icons-material/UploadFile";

import api from "../../api/api";

function UploadMaterial({ courseId, onUploadSuccess }) {

  const [file, setFile] = useState(null);

  const [loading, setLoading] = useState(false);

  const [message, setMessage] = useState("");

  async function handleUpload() {

    if (!file) {

      setMessage("Please choose a PDF file.");

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

        p:4,

        borderRadius:4,

        mb:4,

      }}

    >

      <Typography

        variant="h5"

        fontWeight="bold"

        mb={3}

      >

        📄 Upload Course Material

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

          onChange={(e)=>setFile(e.target.files[0])}

        />

      </Button>

      {file && (

        <Typography

          mt={2}

          color="primary"

        >

          {file.name}

        </Typography>

      )}

      <Box mt={3}>

        <Button

          variant="contained"

          size="large"

          onClick={handleUpload}

          disabled={loading}

          sx={{

            borderRadius:3,

            textTransform:"none",

          }}

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

      </Box>

      {message && (

        <Alert

          severity={

            message.includes("success")

              ? "success"

              : "error"

          }

          sx={{ mt:3 }}

        >

          {message}

        </Alert>

      )}

    </Paper>

  );

}

export default UploadMaterial;