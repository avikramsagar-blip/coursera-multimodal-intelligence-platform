import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
} from "@mui/material";

import api from "../api/api";

function CreateCourse() {
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState(0);
  const [category, setCategory] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [thumbnail, setThumbnail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCreate() {
    setError("");

    if (!title.trim() || !description.trim()) {
      setError("Please provide title and description");
      return;
    }

    try {
      setLoading(true);
      const body = {
        title,
        description,
        price: Number(price),
        category,
        difficulty,
        thumbnail: thumbnail || null,
      };

      const res = await api.post("/courses", body);

      // Navigate to newly created course page
      navigate(`/course/${res.data.course_id}`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || "Failed to create course");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box sx={{ p: 4 }}>
      <Paper sx={{ p: 4, maxWidth: 800, margin: "0 auto" }} elevation={6}>
        <Typography variant="h5" fontWeight="bold" mb={3}>
          Create Course
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <TextField
          label="Title"
          fullWidth
          margin="normal"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <TextField
          label="Description"
          fullWidth
          margin="normal"
          multiline
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <TextField
          label="Category"
          fullWidth
          margin="normal"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />

        <TextField
          label="Difficulty"
          fullWidth
          margin="normal"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
        />

        <TextField
          label="Price"
          fullWidth
          margin="normal"
          type="number"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />

        <TextField
          label="Thumbnail URL (optional)"
          fullWidth
          margin="normal"
          value={thumbnail}
          onChange={(e) => setThumbnail(e.target.value)}
        />

        <Box mt={3} display="flex" gap={2}>
          <Button variant="contained" onClick={handleCreate} disabled={loading}>
            Create
          </Button>
          <Button variant="outlined" onClick={() => navigate(-1)}>
            Cancel
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}

export default CreateCourse;
