import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";

import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Avatar,
  Stack,
  CircularProgress,
  IconButton,
} from "@mui/material";

import SmartToyIcon from "@mui/icons-material/SmartToy";
import PersonIcon from "@mui/icons-material/Person";
import SendIcon from "@mui/icons-material/Send";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DeleteIcon from "@mui/icons-material/Delete";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";

import Layout from "../components/Layout";
import api from "../api/api";

function AITutor() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function askAI() {
    if (!question.trim()) return;

    const userQuestion = question;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: userQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await api.post(
        "/course-rag-chat",
        {
          course_id: Number(id),
          question: userQuestion,
        }
      );

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: response.data.answer,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            error.response?.data?.detail ||
            "Failed to get AI response.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askAI();
    }
  }

  function clearChat() {
    setMessages([]);
  }

  function copyMessage(text) {
    navigator.clipboard.writeText(text);
  }  return (
    <Layout>
      <Box sx={{ maxWidth: 1000, mx: "auto", py: 4 }}>

        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          mb={3}
        >
          <Button
            startIcon={<ArrowBackIcon />}
            variant="outlined"
            onClick={() => navigate(-1)}
          >
            Back
          </Button>

          <Typography
            variant="h4"
            fontWeight="bold"
          >
            🤖 AI Tutor
          </Typography>

          <IconButton
            color="error"
            onClick={clearChat}
          >
            <DeleteIcon />
          </IconButton>
        </Stack>

        <Paper
          elevation={3}
          sx={{
            height: "65vh",
            overflowY: "auto",
            p: 3,
            borderRadius: 4,
            mb: 3,
            bgcolor: "#F8FAFC",
          }}
        >

          {messages.length === 0 && (

            <Typography
              align="center"
              sx={{
                mt: 15,
                color: "text.secondary",
                whiteSpace: "pre-line",
                lineHeight: 2,
                fontSize: 18,
              }}
            >
{`🤖 Welcome to AI Tutor

Ask anything from your uploaded course material.

Examples:

• Explain JWT Authentication

• Summarize Chapter 2

• Difference between FastAPI and Flask

• Generate Interview Questions`}
            </Typography>

          )}

          {messages.map((msg, index) => (

            <Stack
              key={index}
              direction="row"
              spacing={2}
              justifyContent={
                msg.role === "user"
                  ? "flex-end"
                  : "flex-start"
              }
              mb={3}
            >

              {msg.role === "assistant" && (

                <Avatar
                  sx={{
                    bgcolor: "#7C3AED",
                  }}
                >
                  <SmartToyIcon />
                </Avatar>

              )}

              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  maxWidth: "70%",
                  bgcolor:
                    msg.role === "user"
                      ? "#6366F1"
                      : "#EEF2FF",
                  color:
                    msg.role === "user"
                      ? "#fff"
                      : "#000",
                  borderRadius: 3,
                }}
              >

                <ReactMarkdown>
                  {msg.text}
                </ReactMarkdown>

                {msg.role === "assistant" && (

                  <Button
                    size="small"
                    startIcon={<ContentCopyIcon />}
                    sx={{ mt: 1 }}
                    onClick={() =>
                      copyMessage(msg.text)
                    }
                  >
                    Copy
                  </Button>

                )}

              </Paper>

              {msg.role === "user" && (

                <Avatar
                  sx={{
                    bgcolor: "#4F46E5",
                  }}
                >
                  <PersonIcon />
                </Avatar>

              )}

            </Stack>

          ))}

          {loading && (

            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
            >

              <Avatar
                sx={{
                  bgcolor: "#7C3AED",
                }}
              >
                <SmartToyIcon />
              </Avatar>

              <CircularProgress size={22} />

              <Typography fontWeight="bold">
                Thinking...
              </Typography>

            </Stack>

          )}

        </Paper>

        <Stack
          direction="row"
          spacing={2}
        >

          <TextField
            fullWidth
            multiline
            minRows={2}
            maxRows={5}
            variant="outlined"
            placeholder="Ask your question..."
            value={question}
            onChange={(e) =>
              setQuestion(e.target.value)
            }
            onKeyDown={handleKeyDown}
          />

          <Button
            variant="contained"
            size="large"
            endIcon={<SendIcon />}
            disabled={loading}
            onClick={askAI}
            sx={{
              minWidth: 170,
              borderRadius: 3,
            }}
          >
            Ask AI
          </Button>

        </Stack>

      </Box>
    </Layout>
  );
}

export default AITutor;