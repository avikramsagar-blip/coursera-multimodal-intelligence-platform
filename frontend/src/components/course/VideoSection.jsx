import {
  useState,
  useRef,
  useEffect,
} from "react"; 
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  Divider,
  Button,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Stack,
} from "@mui/material";

import PlayCircleFilledIcon from "@mui/icons-material/PlayCircleFilled";
import OndemandVideoIcon from "@mui/icons-material/OndemandVideo";
import DeleteIcon from "@mui/icons-material/Delete";
import CloseIcon from "@mui/icons-material/Close";

import api from "../../api/api";
function VideoSection({
  videos,
  seekTime,
  targetVideoId,
  onRefresh,
}) {


  const [selectedVideo, setSelectedVideo] =
    useState(null);
  const videoRef = useRef(null);
  useEffect(() => {
  if (
    videoRef.current &&
    seekTime !== null &&
    seekTime !== undefined
  ) {
    videoRef.current.currentTime =
      Number(seekTime);

    videoRef.current.play().catch(() => {});
  }
}, [seekTime]);

  const [deleting, setDeleting] =
    useState(false);

  function handleWatch(video) {
    setSelectedVideo(video);
  }

  function handleClose() {
    setSelectedVideo(null);
  }
  useEffect(() => {
  if (
    targetVideoId == null ||
    !videos ||
    videos.length === 0
  ) {
    return;
  }

  const targetVideo = videos.find(
    (video) =>
      Number(video.video_id) ===
      Number(targetVideoId)
  );

  if (targetVideo) {
    setSelectedVideo(targetVideo);
  }
}, [targetVideoId, videos]);

  async function handleDelete(videoId) {
    const ok = window.confirm(
      "Are you sure you want to delete this video?"
    );

    if (!ok) return;

    try {
      setDeleting(true);

      await api.delete(
        `/videos/${videoId}`
      );

      if (selectedVideo?.video_id === videoId) {
        setSelectedVideo(null);
      }

      if (onRefresh) {
        await onRefresh();
      }
    } catch (error) {
      console.error(
        "Video delete error:",
        error
      );

      alert(
        error.response?.data?.detail ||
          "Unable to delete video."
      );
    } finally {
      setDeleting(false);
    }
  }

  function isYouTubeUrl(url) {
    if (!url) return false;

    return (
      url.includes("youtube.com") ||
      url.includes("youtu.be")
    );
  }

  function getYouTubeEmbedUrl(
  url,
  startTime = 0
) {
  try {
    const parsedUrl = new URL(url);

    let videoId = "";

    if (
      parsedUrl.hostname.includes(
        "youtu.be"
      )
    ) {
      videoId =
        parsedUrl.pathname.substring(1);
    } else {
      videoId =
        parsedUrl.searchParams.get("v");
    }

    if (!videoId) {
      return url;
    }

    const start = Math.max(
      0,
      Math.floor(
        Number(startTime) || 0
      )
    );

    return `https://www.youtube.com/embed/${videoId}?start=${start}&autoplay=1`;
  } catch {
    return url;
  }
}

return (
  <>
    <Paper
      elevation={3}
      sx={{
        p: 4,
        borderRadius: 4,
        mb: 4,
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        🎥 Course Videos

        <Chip
          icon={
            <OndemandVideoIcon />
          }
          label={`${videos.length} Videos`}
          color="primary"
        />
      </Box>

      {videos.length === 0 ? (
        <Typography color="text.secondary">
          No videos available for this
          course.
        </Typography>
      ) : (
        <List>
          {videos.map(
            (video, index) => (
              <Box
                key={video.video_id}
              >
                <ListItem
                  secondaryAction={
                    <Stack
                      direction="row"
                      spacing={1}
                    >
                      <Button
                        variant="contained"
                        size="small"
                        startIcon={
                          <PlayCircleFilledIcon />
                        }
                        onClick={() =>
                          handleWatch(video)
                        }
                      >
                        Watch
                      </Button>

                      <IconButton
                        color="error"
                        disabled={deleting}
                        onClick={() =>
                          handleDelete(
                            video.video_id
                          )
                        }
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Stack>
                  }
                >
                  <ListItemAvatar>
                    <Avatar
                      sx={{
                        bgcolor:
                          "primary.main",
                      }}
                    >
                      <PlayCircleFilledIcon />
                    </Avatar>
                  </ListItemAvatar>

                  <ListItemText
                    primary={
                      video.title ||
                      "Untitled Video"
                    }
                    secondary={
                      video.description ||
                      "Course Video"
                    }
                  />
                </ListItem>

                {index !==
                  videos.length - 1 && (
                  <Divider />
                )}
              </Box>
            )
          )}
        </List>
      )}
    </Paper>

    {/* ========================= */}
    {/* VIDEO PLAYER DIALOG */}
    {/* ========================= */}

    <Dialog
      open={Boolean(selectedVideo)}
      onClose={handleClose}
      fullWidth
      maxWidth="md"
    >
      <DialogTitle>
        <Box
          sx={{
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
          }}
        >
          <Typography
            variant="h6"
            fontWeight="bold"
          >
            {selectedVideo?.title ||
              "Course Video"}
          </Typography>

          <IconButton
            onClick={handleClose}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        {selectedVideo?.video_url && (
          <Box sx={{ mt: 1 }}>
            {isYouTubeUrl(
              selectedVideo.video_url
            ) ? (
              <Box
                sx={{
                  position: "relative",
                  paddingTop: "56.25%",
                  width: "100%",
                }}
              >
                <iframe
                  src={getYouTubeEmbedUrl(
                    selectedVideo.video_url,
                    seekTime
                  )}
                  title={
                    selectedVideo.title ||
                    "Course Video"
                  }
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    border: 0,
                    borderRadius: "12px",
                  }}
                />
              </Box>
            ) : (
              <video
                ref={videoRef}
                controls
                width="100%"
                style={{
                  borderRadius: "12px",
                  display: "block",
                }}
                src={
                  selectedVideo.video_url.startsWith(
                    "http"
                  )
                    ? selectedVideo.video_url
                    : `${"https://coursera-multimodal-intelligence-platform-6wvy.onrender.com"}${selectedVideo.video_url}`
                }
              >
                Your browser does not
                support video playback.
              </video>
            )}

            <Typography
              sx={{ mt: 2 }}
              color="text.secondary"
            >
              {selectedVideo.description ||
                "Course Video"}
            </Typography>

            {selectedVideo.duration && (
              <Chip
                label={`${selectedVideo.duration} seconds`}
                size="small"
                sx={{ mt: 1 }}
              />
            )}
          </Box>
        )}
      </DialogContent>
    </Dialog>
  </>
);

}
export default VideoSection;


