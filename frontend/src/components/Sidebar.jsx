import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
} from "@mui/material";

import DashboardIcon from "@mui/icons-material/Dashboard";
import SchoolIcon from "@mui/icons-material/School";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import PersonIcon from "@mui/icons-material/Person";

import { useNavigate, useLocation } from "react-router-dom";

const drawerWidth = 240;

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      text: "Dashboard",
      icon: <DashboardIcon />,
      path: "/dashboard",
    },
    {
      text: "Courses",
      icon: <SchoolIcon />,
      path: "/dashboard",
    },
    {
      text: "AI Tutor",
      icon: <SmartToyIcon />,
      path: "/ai-tutor",
    },
    {
      text: "Profile",
      icon: <PersonIcon />,
      path: "/profile",
    },
  ];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,

        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
          borderRight: "1px solid #E5E7EB",
          backgroundColor: "#FFFFFF",

          top: "64px",
          height: "calc(100vh - 64px)",

          paddingTop: "20px",
          paddingLeft: "12px",
          paddingRight: "12px",
        },
      }}
    >
      <Box>
        <Typography
          variant="subtitle1"
          fontWeight="bold"
          color="primary"
          sx={{
            mb: 3,
            ml: 2,
          }}
        >
          Navigation
        </Typography>

        <List>
          {menuItems.map((item) => (
            <ListItem
              disablePadding
              key={item.text}
              sx={{
                mb: 1,
              }}
            >
              <ListItemButton
                onClick={() => navigate(item.path)}
                selected={location.pathname === item.path}
                sx={{
                  borderRadius: 2,
                  py: 0.8,

                  "&.Mui-selected": {
                    backgroundColor: "#1976D2",
                    color: "#fff",
                  },

                  "&.Mui-selected:hover": {
                    backgroundColor: "#1565C0",
                  },

                  "&.Mui-selected .MuiListItemIcon-root": {
                    color: "#fff",
                  },

                  "&:hover": {
                    backgroundColor: "#E3F2FD",
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 42,
                    color:
                      location.pathname === item.path
                        ? "#fff"
                        : "#1976D2",
                  }}
                >
                  {item.icon}
                </ListItemIcon>

                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontWeight: 600,
                    fontSize: 15,
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
    </Drawer>
  );
}

export default Sidebar;