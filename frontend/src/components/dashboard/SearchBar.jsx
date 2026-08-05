import {
  TextField,
  InputAdornment,
} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";

function SearchBar({
  value,
  onChange,
}) {
  return (
    <TextField
      fullWidth
      placeholder="Search Courses..."
      value={value}
      onChange={onChange}
      sx={{ mb: 4 }}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
      }}
    />
  );
}

export default SearchBar;