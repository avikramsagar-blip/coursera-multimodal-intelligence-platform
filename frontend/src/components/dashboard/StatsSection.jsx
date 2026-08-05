import {
  Box,
  Grid,
} from "@mui/material";

import SchoolIcon from "@mui/icons-material/School";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import DescriptionIcon from "@mui/icons-material/Description";
import VideoLibraryIcon from "@mui/icons-material/VideoLibrary";

import StatCard from "./StatCard";

function StatsSection({ totalCourses }) {
  return (
    <Box mb={5}>
      <Grid container spacing={3}>

        <Grid size={{ xs:12, sm:6, md:3 }}>
          <StatCard
            title="Courses"
            value={totalCourses}
            icon={<SchoolIcon />}
            color="#1976d2"
          />
        </Grid>

        <Grid size={{ xs:12, sm:6, md:3 }}>
          <StatCard
            title="AI Tutor"
            value="24"
            icon={<SmartToyIcon />}
            color="#7B1FA2"
          />
        </Grid>

        <Grid size={{ xs:12, sm:6, md:3 }}>
          <StatCard
            title="Materials"
            value="12"
            icon={<DescriptionIcon />}
            color="#2E7D32"
          />
        </Grid>

        <Grid size={{ xs:12, sm:6, md:3 }}>
          <StatCard
            title="Videos"
            value="8"
            icon={<VideoLibraryIcon />}
            color="#ED6C02"
          />
        </Grid>

      </Grid>
    </Box>
  );
}

export default StatsSection;