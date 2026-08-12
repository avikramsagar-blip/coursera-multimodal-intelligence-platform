import { useState } from "react";

import {
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
} from "@mui/material";

import OndemandVideoIcon from "@mui/icons-material/OndemandVideo";
import UploadFileIcon from "@mui/icons-material/UploadFile";

import api from "../../api/api";

function UploadAudio({
  courseId,
  onUploadSuccess,
}) {
  const [title, setTitle] =
    useState("");

  const [description, setDescription] =
    useState("");


  const [orderNo, setOrderNo] =
    useState("");

  const [file, setFile] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  function handleFileChange(e) {
    const selectedFile =
      e.target.files?.[0];

    if (!selectedFile) {
      setFile(null);
      return;
    }

    const allowedTypes = [
      "audio/mpeg",
      "audio/webm",
      "audio/ogg",
      "audio/mp4",
    ];

    if (
      !allowedTypes.includes(
        selectedFile.type
      )
    ) {
      setError(
        "Please select a valid audio file: MP3, WAV, OGG or M4A."
      );

      e.target.value = "";
      setFile(null);

      return;
    }

    setError("");
    setFile(selectedFile);
  }

  async function handleSubmit(e) {
    e.preventDefault();

    setError("");
    setSuccess("");

    if (!title.trim()) {
      setError(
        "Audio title is required."
      );
      return;
    }

    if (!file) {
      setError(
        "Please select a audio file."
      );
      return;
    }

  

    try {
      setLoading(true);

      const formData =
        new FormData();

      formData.append(
        "course_id",
        courseId
      );

      formData.append(
        "title",
        title.trim()
      );

      formData.append(
        "description",
        description.trim()
      );

      

      formData.append(
        "order_no",
        orderNo === ""
          ? 0
          : Number(orderNo)
      );

      formData.append(
        "file",
        file
      );

      await api.post(
        "/upload-course-audio",
        formData,
        {
          headers: {
            "Content-Type":
              "multipart/form-data",
          },
        }
      );

      setTitle("");
      setDescription("");
      setOrderNo("");
      setFile(null);

      const fileInput =
        document.getElementById(
          "audio-file-input"
        );

      if (fileInput) {
        fileInput.value = "";
      }

      setSuccess(
        "Audio uploaded successfully."
      );

      if (onUploadSuccess) {
        await onUploadSuccess();
      }
    } catch (err) {
      console.error(
        "Video upload error:",
        err
      );

      const detail =
        err.response?.data?.detail;

      let errorMessage =
        "Unable to upload audio.";

      if (Array.isArray(detail)) {
        errorMessage = detail
          .map(
            (item) =>
              item.msg ||
              "Invalid input"
          )
          .join(", ");
      } else if (
        typeof detail === "string"
      ) {
        errorMessage = detail;
      }

      setError(errorMessage);
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
        mt: 4,
      }}
    >
      <Stack
        direction="row"
        spacing={1}
        alignItems="center"
        mb={3}
      >
        <OndemandVideoIcon
          color="primary"
        />

        <Typography
          variant="h6"
          fontWeight="bold"
        >
          Upload Course Audio
        </Typography>
      </Stack>

      {error && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() =>
            setError("")
          }
        >
          {error}
        </Alert>
      )}

      {success && (
        <Alert
          severity="success"
          sx={{ mb: 2 }}
          onClose={() =>
            setSuccess("")
          }
        >
          {success}
        </Alert>
      )}

      <form
        onSubmit={handleSubmit}
      >
        <Stack spacing={2}>

          <TextField
            fullWidth
            label="Audio Title"
            value={title}
            onChange={(e) =>
              setTitle(
                e.target.value
              )
            }
          />

          <TextField
            fullWidth
            multiline
            minRows={2}
            label="Description"
            value={description}
            onChange={(e) =>
              setDescription(
                e.target.value
              )
            }
          />

          <Button
            component="label"
            variant="outlined"
            startIcon={
              <UploadFileIcon />
            }
          >
            {file
              ? file.name
              : "Select Audio File"}

            <input
              id="audio-file-input"
              type="file"
              hidden
              accept="audio/mpeg,audio/webm,audio/ogg,audio/mp4"
              onChange={
                handleFileChange
              }
            />
          </Button>

          

          <TextField
            fullWidth
            type="number"
            label="Order Number"
            value={orderNo}
            onChange={(e) =>
              setOrderNo(
                e.target.value
              )
            }
            inputProps={{
              min: 0,
            }}
          />

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={loading}
            startIcon={
              <UploadFileIcon />
            }
          >
            {loading
              ? "Uploading..."
              : "Upload Audio"}
          </Button>

        </Stack>
      </form>
    </Paper>
  );
}

export default UploadAudio;

