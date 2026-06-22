require "nvchad.autocmds"

local autocmd = vim.api.nvim_create_autocmd

if not vim.g.neovide then
  autocmd({ "VimEnter", "VimLeave" }, {
    callback = function(args)
      if args.event == "VimEnter" then
        vim.cmd "silent !alacritty msg config window.padding.x=0 window.padding.y=0"
      else
        vim.cmd "silent !alacritty msg config window.padding.x=20 window.padding.y=20"
      end
    end,
  })
end

-- autocmd({ "tabnew" }, {
--   callback = function(args)
--     vim.print { args.buf, vim.api.nvim_buf_get_name(args.buf), args.event }
--   end,
-- })
