local function prepare()
  -- Check the assets produced by the user's normal interactive build hooks.
  local languages = {
    'bash', 'c', 'cmake', 'comment', 'cpp', 'csv', 'diff', 'fish', 'go',
    'json', 'lua', 'make', 'markdown', 'markdown_inline', 'meson', 'nix',
    'python', 'ron', 'rust', 'toml', 'vim', 'vimdoc', 'yaml',
  }
  for _, language in ipairs(languages) do
    local ok, loaded = pcall(vim.treesitter.language.add, language)
    assert(ok and loaded, 'Parser not prepared: ' .. language)
  end
  vim.cmd.UpdateRemotePlugins()
  local registration = vim.fn.stdpath('data') .. '/rplugin.vim'
  assert(vim.fn.filereadable(registration) == 1, 'Remote plugins were not registered')
  assert(table.concat(vim.fn.readfile(registration), '\n'):find('molten'), 'Molten provider was not registered')
  -- Blink downloads its release-native library asynchronously at startup.
  assert(vim.wait(120000, function()
    return #vim.api.nvim_get_runtime_file('target/release/libblink_cmp_fuzzy.so', true) > 0
  end, 100), 'Blink native library was not prepared')
end
local ok, err = xpcall(prepare, debug.traceback)
if not ok then
  io.stderr:write(tostring(err) .. '\n')
  vim.cmd.cquit(1)
end
vim.cmd.quitall()
