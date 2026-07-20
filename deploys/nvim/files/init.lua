vim.cmd("syntax enable")
vim.cmd("filetype plugin indent on")

vim.o.number = true
vim.o.expandtab = true
vim.o.shiftwidth = 2
vim.o.tabstop = 2

vim.api.nvim_create_autocmd("FileType", {
    pattern = "yaml",
    callback = function()
        vim.wo.foldmethod = "indent"
        vim.wo.foldlevel = 99
        vim.bo.shiftwidth = 2
        vim.bo.expandtab = true
    end,
})