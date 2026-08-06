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
} from "@mui/material";

import PlayCircleFilledIcon from "@mui/icons-material/PlayCircleFilled";
import OndemandVideoIcon from "@mui/icons-material/OndemandVideo";

function VideoSection({ videos }) {
  return (
    <Paper
      elevation={3}
      sx={{
        p: 4,
        borderRadius: 4,
        mb: 4,
      }}
    >
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography
          variant="h5"
          fontWeight="bold"
        >
          🎥 Course Videos
        </Typography>

        <Chip
          icon={<OndemandVideoIcon />}
          label={`${videos.length} Videos`}
          color="primary"
        />
      </Box>

      {videos.length === 0 ? (
        <Typography color="text.secondary">
          No videos available for this course.
        </Typography>
      ) : (
        <List>

          {videos.map((video, index) => (

            <Box key={video.video_id}>

              <ListItem
                secondaryAction={
                  <Button
                    variant="contained"
                    size="small"
                  >
                    Watch
                  </Button>
                }
              >

                <ListItemAvatar>

                  <Avatar
                    sx={{
                      bgcolor: "primary.main",
                    }}
                  >
                    <PlayCircleFilledIcon />
                  </Avatar>

                </ListItemAvatar>

                <ListItemText
                  primary={video.title}
                  secondary={
                    video.description ||
                    "Course Video"
                  }
                />

              </ListItem>

              {index !== videos.length - 1 && (
                <Divider />
              )}

            </Box>

          ))}

        </List>
      )}
    </Paper>
  );
}

export default VideoSection;