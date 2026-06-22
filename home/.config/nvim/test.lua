local mymaps = {
  {
    "n",
    "<leader>t",
    "<cmd> Telescope <CR>",
    { noremap = true, silent = true },
  },
  {
    "n",
    "<leader>f",
    "<cmd> Telescope find_files <CR>",
    { noremap = true, silent = true },
  },
}

for _, map in ipairs(mymaps) do
  vim.keymap.set(map[1], map[2], map[3], map[4])
end
