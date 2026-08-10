import React, { useEffect, useState } from "react";

import {
  Box,
  Paper,
  Typography,
  Avatar,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  TextField,
  Button,
  LinearProgress,
} from "@mui/material";
import LockIcon from "@mui/icons-material/Lock";
import PersonIcon from "@mui/icons-material/Person";
import EmailIcon from "@mui/icons-material/Email";
import SchoolIcon from "@mui/icons-material/School";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import api from "../api/api";

function Profile() {
  const [user, setUser] = useState(null);
  const [courses, setCourses] = useState([]);
  const [courseDetails, setCourseDetails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [editing, setEditing] = useState(false);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [changingPassword, setChangingPassword] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // --------------------------------
  // Load profile and courses
  // --------------------------------

  useEffect(() => {
    fetchProfile();
    fetchCourses();
  }, []);

  // --------------------------------
  // Get logged-in user
  // --------------------------------

  async function fetchProfile() {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/me");

      setUser(response.data);

      setFullName(response.data.full_name || "");
      setEmail(response.data.email || "");
    } catch (err) {
      console.error("Profile error:", err);

      setError("Unable to load profile");
    } finally {
      setLoading(false);
    }
  }

  // --------------------------------
  // Get enrolled courses
  // --------------------------------

  async function fetchCourses() {
  try {
    const response = await api.get("/my-courses");

    const enrollments = response.data;

    setCourses(enrollments);

    const details = await Promise.all(
      enrollments.map(async (enrollment) => {
        try {
          const courseResponse = await api.get(
            `/courses/${enrollment.course_id}`
          );

          return {
            ...enrollment,
            course: courseResponse.data,
          };
        } catch (err) {
          console.error(
            `Unable to load course ${enrollment.course_id}`,
            err
          );

          return {
            ...enrollment,
            course: null,
          };
        }
      })
    );

    setCourseDetails(details);
  } catch (err) {
    console.error("Courses error:", err);
  }
}
  // --------------------------------
  // Learning statistics
  // --------------------------------

  const enrolledCourses = courses.length;

  const completedCourses = courses.filter(
    (course) => course.completed
  ).length;

  // --------------------------------
  // Start editing
  // --------------------------------

  function handleEdit() {
    setSuccess("");
    setError("");

    setFullName(user.full_name || "");
    setEmail(user.email || "");

    setEditing(true);
  }

  // --------------------------------
  // Cancel editing
  // --------------------------------

  function handleCancel() {
    setFullName(user.full_name || "");
    setEmail(user.email || "");

    setError("");
    setEditing(false);
  }

  // --------------------------------
  // Save profile
  // --------------------------------

  async function handleSave() {
    if (!fullName.trim() || !email.trim()) {
      setError("Name and email are required");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const response = await api.put(
        `/users/${user.user_id}`,
        {
          full_name: fullName,
          email: email,
        }
      );

      setUser(response.data);

      setFullName(
        response.data.full_name || ""
      );

      setEmail(
        response.data.email || ""
      );

      setEditing(false);

      setSuccess(
        "Profile updated successfully"
      );
    } catch (err) {
      console.error("Update profile error:", err);

      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Unable to update profile"
      );
    } finally {
      setSaving(false);
    }
  }

  // --------------------------------
  // Loading screen
  // --------------------------------
  async function handleChangePassword() {
  if (
    !currentPassword ||
    !newPassword ||
    !confirmPassword
  ) {
    setError("Please fill all password fields");
    return;
  }

  if (newPassword !== confirmPassword) {
    setError(
      "New password and confirm password do not match"
    );
    return;
  }

  if (newPassword.length < 6) {
    setError(
      "New password must be at least 6 characters"
    );
    return;
  }

  try {
    setChangingPassword(true);
    setError("");
    setSuccess("");

    const response = await api.put(
      "/change-password",
      {
        current_password: currentPassword,
        new_password: newPassword,
      }
    );

    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");

    setSuccess(
      response.data.message ||
        "Password changed successfully"
    );
  } catch (err) {
    console.error(
      "Change password error:",
      err
    );

    const detail =
      err.response?.data?.detail;

    setError(
      typeof detail === "string"
        ? detail
        : "Unable to change password"
    );
  } finally {
    setChangingPassword(false);
  }
}

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: "70vh",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // --------------------------------
  // Profile failed
  // --------------------------------

  if (!user) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error">
          Unable to load profile
        </Alert>
      </Box>
    );
  }

  // --------------------------------
  // Main UI
  // --------------------------------

  return (
    <Box sx={{ p: 4 }}>
      {/* Page title */}

      <Typography
        variant="h4"
        fontWeight="bold"
        mb={4}
      >
        My Profile
      </Typography>

      {/* Error message */}

      {error && (
        <Alert
          severity="error"
          sx={{
            mb: 2,
            maxWidth: 900,
          }}
        >
          {error}
        </Alert>
      )}

      {/* Success message */}

      {success && (
        <Alert
          severity="success"
          sx={{
            mb: 2,
            maxWidth: 900,
          }}
        >
          {success}
        </Alert>
      )}

      {/* Main profile card */}

      <Paper
        elevation={3}
        sx={{
          p: 4,
          borderRadius: 3,
          maxWidth: 900,
        }}
      >
        {/* --------------------------------
            Profile Header
        -------------------------------- */}

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 3,
            mb: 4,
          }}
        >
          <Avatar
            sx={{
              width: 90,
              height: 90,
              fontSize: 40,
            }}
          >
            <PersonIcon fontSize="large" />
          </Avatar>

          <Box>
            <Typography
              variant="h5"
              fontWeight="bold"
            >
              {user.full_name}
            </Typography>

            <Typography
              color="text.secondary"
            >
              {user.email}
            </Typography>

            <Chip
              label={user.role || "Student"}
              size="small"
              sx={{
                mt: 1,
              }}
            />
          </Box>
        </Box>

        {/* --------------------------------
            EDIT MODE
        -------------------------------- */}

        {editing ? (
          <Box>
            <Typography
              variant="h6"
              fontWeight="bold"
              mb={3}
            >
              Edit Profile
            </Typography>

            {/* Full Name */}

            <TextField
              fullWidth
              label="Full Name"
              value={fullName}
              onChange={(e) =>
                setFullName(
                  e.target.value
                )
              }
              sx={{
                mb: 2,
              }}
            />

            {/* Email */}

            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(
                  e.target.value
                )
              }
              sx={{
                mb: 3,
              }}
            />

            {/* Buttons */}

            <Box
              sx={{
                display: "flex",
                gap: 2,
              }}
            >
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : "Save Changes"}
              </Button>

              <Button
                variant="outlined"
                onClick={handleCancel}
                disabled={saving}
              >
                Cancel
              </Button>
            </Box>
          </Box>
        ) : (
          <>
            {/* --------------------------------
                Personal Information
            -------------------------------- */}

            <Typography
              variant="h6"
              fontWeight="bold"
              mb={2}
            >
              Personal Information
            </Typography>

            <Grid
              container
              spacing={3}
            >
              {/* Full Name */}

              <Grid
                item
                xs={12}
                md={6}
              >
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                  }}
                >
                  <PersonIcon />

                  <Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                    >
                      Full Name
                    </Typography>

                    <Typography
                      fontWeight="medium"
                    >
                      {user.full_name}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>

              {/* Email */}

              <Grid
                item
                xs={12}
                md={6}
              >
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                  }}
                >
                  <EmailIcon />

                  <Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                    >
                      Email
                    </Typography>

                    <Typography
                      fontWeight="medium"
                    >
                      {user.email}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>

              {/* Role */}

              <Grid
                item
                xs={12}
                md={6}
              >
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                  }}
                >
                  <SchoolIcon />

                  <Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                    >
                      Role
                    </Typography>

                    <Typography
                      fontWeight="medium"
                    >
                      {user.role ||
                        "Student"}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
            </Grid>

            {/* Edit button */}

            <Button
              variant="contained"
              sx={{
                mt: 4,
              }}
              onClick={handleEdit}
            >
              Edit Profile
            </Button>
            {/* Change Password */}

<Typography
  variant="h6"
  fontWeight="bold"
  sx={{
    mt: 5,
    mb: 2,
  }}
>
  Change Password
</Typography>

<Paper
  variant="outlined"
  sx={{
    p: 3,
    borderRadius: 3,
  }}
>
  <Box
    sx={{
      display: "flex",
      alignItems: "center",
      gap: 2,
      mb: 3,
    }}
  >
    <LockIcon />

    <Typography fontWeight="bold">
      Update your password
    </Typography>
  </Box>

  <TextField
    fullWidth
    label="Current Password"
    type="password"
    value={currentPassword}
    onChange={(e) =>
      setCurrentPassword(e.target.value)
    }
    sx={{ mb: 2 }}
  />

  <TextField
    fullWidth
    label="New Password"
    type="password"
    value={newPassword}
    onChange={(e) =>
      setNewPassword(e.target.value)
    }
    sx={{ mb: 2 }}
  />

  <TextField
    fullWidth
    label="Confirm New Password"
    type="password"
    value={confirmPassword}
    onChange={(e) =>
      setConfirmPassword(e.target.value)
    }
    sx={{ mb: 3 }}
  />

  <Button
    variant="contained"
    onClick={handleChangePassword}
    disabled={changingPassword}
  >
    {changingPassword
      ? "Changing Password..."
      : "Change Password"}
  </Button>
</Paper>

            {/* --------------------------------
                Learning Overview
            -------------------------------- */}

            <Typography
              variant="h6"
              fontWeight="bold"
              sx={{
                mt: 5,
                mb: 2,
              }}
            >
              Learning Overview
            </Typography>

            <Grid
              container
              spacing={3}
            >
              {/* Enrolled Courses */}

              <Grid
                item
                xs={12}
                md={6}
              >
                <Paper
                  variant="outlined"
                  sx={{
                    p: 3,
                    textAlign: "center",
                    borderRadius: 3,
                  }}
                >
                  <Typography
                    variant="h3"
                    fontWeight="bold"
                  >
                    {enrolledCourses}
                  </Typography>

                  <Typography
                    color="text.secondary"
                  >
                    Courses Enrolled
                  </Typography>
                </Paper>
              </Grid>

              {/* Completed Courses */}

              <Grid
                item
                xs={12}
                md={6}
              >
                <Paper
                  variant="outlined"
                  sx={{
                    p: 3,
                    textAlign: "center",
                    borderRadius: 3,
                  }}
                >
                  <Typography
                    variant="h3"
                    fontWeight="bold"
                  >
                    {completedCourses}
                  </Typography>

                  <Typography
                    color="text.secondary"
                  >
                    Courses Completed
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
            {/* --------------------------------
    My Courses
-------------------------------- */}

<Typography
  variant="h6"
  fontWeight="bold"
  sx={{
    mt: 5,
    mb: 2,
  }}
>
  My Courses
</Typography>

{courseDetails.length === 0 ? (
  <Paper
    variant="outlined"
    sx={{
      p: 3,
      textAlign: "center",
      borderRadius: 3,
    }}
  >
    <Typography color="text.secondary">
      You are not enrolled in any courses yet.
    </Typography>
  </Paper>
) : (
  <Grid container spacing={3}>
    {courseDetails.map((item) => {
      const progress = item.progress || 0;

      return (
        <Grid
          item
          xs={12}
          md={6}
          key={item.course_id}
        >
          <Paper
            elevation={2}
            sx={{
              p: 3,
              borderRadius: 3,
              height: "100%",
            }}
          >
            <Typography
              variant="h6"
              fontWeight="bold"
            >
              {item.course?.title ||
                `Course ${item.course_id}`}
            </Typography>

            <Typography
              color="text.secondary"
              sx={{ mt: 1 }}
            >
              {item.course?.category ||
                "Course"}
            </Typography>

            <Box sx={{ mt: 3 }}>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  mb: 1,
                }}
              >
                <Typography variant="body2">
                  Progress
                </Typography>

                <Typography
                  variant="body2"
                  fontWeight="bold"
                >
                  {progress}%
                </Typography>
              </Box>

              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 8,
                  borderRadius: 5,
                }}
              />
            </Box>

            <Box
              sx={{
                mt: 3,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              {item.completed ? (
                <Chip
                  label="Completed"
                  color="success"
                  size="small"
                />
              ) : (
                <Chip
                  label="In Progress"
                  color="primary"
                  size="small"
                />
              )}

              <Button
                size="small"
                variant="outlined"
                startIcon={<PlayArrowIcon />}
                onClick={() =>
                  window.location.href =
                    `/courses/${item.course_id}`
                }
              >
                Continue
              </Button>
            </Box>
          </Paper>
        </Grid>
      );
    })}
  </Grid>
)}
          </>
        )}
      </Paper>
    </Box>
  );
}

export default Profile;