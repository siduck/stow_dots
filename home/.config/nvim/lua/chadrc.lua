--@type ChadrcConfig
local M = {}

M.base46 = {
  theme = "chocolate",
  transparency = false,
  hl_add = require "hl",
  -- integrations = { "markview", "navic" },
  -- hl_override = {
  --   ["@comment"] = { italic = true },
  --   Function = { italic = true },
  --   ["@function.call"] = { italic = true, fg = "red" },
  -- },
}

M.ui = {
  cmp = { style = "atom" },
  telescope = { style = "bordered" },
  statusline = { theme = "minimal", separator_style = "round" },
  tabufline = { lazyload = false },
}

M.nvdash = {
  -- load_on_startup = true,
  -- buttons = require "nvdash"
}

M.term = {
  winopts = { scl = "yes" },
  sizes = { vsp = 0.4 },
}

return M
