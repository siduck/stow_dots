--@type ChadrcConfig
local M = {}

M.base46 = {
  theme = "scaryforest",
  transparency = false,
  integrations = { "markview", "navic" },
  -- hl_override = {
  --   ["@comment"] = { italic = true },
  --   Function = { italic = true },
  --   ["@function.call"] = { italic = true, fg = "red" },
  -- },

}

M.ui = {
  cmp = { style = "atom" },
  telescope = { style = "bordered" },
  -- statusline = { theme = "minimal", separator_style = "round" },
  tabufline = { lazyload = false },
}

M.nvdash = {
  -- load_on_startup = true
}

M.term = {
  winopts = { scl = "yes" },
  -- base46_colors = true,
}

return M
