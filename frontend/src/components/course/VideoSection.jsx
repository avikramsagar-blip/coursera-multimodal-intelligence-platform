import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  Avatar,
  ListItemText,
  Divider,
  Button,
  Box,
} from "@mui/material";

import PlayCircleFilledIcon from "@mui/icons-material/PlayCircleFilled";

function VideoSection({ videos = [] }) {
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
        🎥 Course Videos
      </Typography>

      {videos.length === 0 ? (

        <Typography color="text.secondary">
          No videos available.
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
                      bgcolor: "#1976D2",
                    }}
                  >
                    <PlayCircleFilledIcon />
                  </Avatar>

                </ListItemAvatar>

                <ListItemText
                  primary={video.title}
                  secondary={
                    video.description
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