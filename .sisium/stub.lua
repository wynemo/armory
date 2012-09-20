--pandora manager 是否在注册表中
function GetPandoraPath()
    subkey = "SOFTWARE\\PandoraManager"
    value_name = "InstallPath"
    value = {0}
    path = ""
    result = RegGetValue(HKEY_LOCAL_MACHINE,L(subkey),L(value_name),RRF_RT_REG_SZ,value)
    if result == 0 then
        path = value.data
    end
    return L(path)
end

path = GetPandoraPath()
if FileIsExist(path) == true then
    --http://msdn.microsoft.com/en-us/library/windows/desktop/ms682425(v=vs.85).aspx
    --says quotation marks around the executable path
    --path = L"\""..path..L"\""
    if ExcuteInstall(path) == true then
        print("success")
    else
        if IDOK == LuaMessageBox(L"您还未安装潘多拉游戏管家,点击确定立即安装(运行此游戏需要安装潘多拉游戏管家)",
            L"提示",MB_OKCANCEL) then
            StartInstaller()
        end
    end
else
    if IDOK == LuaMessageBox(L"您还未安装潘多拉游戏管家,点击确定立即安装(运行此游戏需要安装潘多拉游戏管家)",
        L"提示",MB_OKCANCEL) then
        StartInstaller()
    end
end
