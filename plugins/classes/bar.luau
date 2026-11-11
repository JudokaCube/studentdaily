-- Calendar icon at rest; gently reveal the live schedule on hover.
local label = "StudentDaily"
local progress = 0
local target = 0
local hovering = false
local expandUntil = 0
local lastPoll = 0
local busy = false
local renderedText = nil

local function render()
    local count = math.floor((utf8.len(label) or #label) * progress + 0.5)
    local stop = utf8.offset(label, count + 1)
    local text = count == 0 and "" or (stop and label:sub(1, stop - 1) or label)
    if text ~= renderedText then barWidget.setText(text); renderedText = text end
end

local function poll()
    if busy then return end
    busy = true
    lastPoll = os.time()
    noctalia.runAsync('"$HOME/.local/bin/classes" status --json', function(result)
        busy = false
        local data = result.exitCode == 0 and noctalia.json.decode(result.stdout) or nil
        if data and type(data) == "table" then
            label = data.text or "StudentDaily"
            expandUntil = data.expandUntil or 0
            barWidget.setColor(data.textColor or "#88c0d0")
            barWidget.setGlyphColor(data.glyphColor or "#88c0d0")
            barWidget.setTooltip(data.tips)
        else
            label = "Open schedule"
            barWidget.setTooltip("Click to open StudentDaily")
        end
        render()
    end, 5000)
end

function update()
    target = (hovering or os.time() < expandUntil) and 1 or 0
    if os.time() - lastPoll >= 15 then poll() end
    if math.abs(progress - target) < 0.01 then
        progress = target
        noctalia.setUpdateInterval(1000)
    else
        progress = progress + (target - progress) * 0.22
        noctalia.setUpdateInterval(16)
    end
    render()
end

function onHover(isHovering)
    hovering = isHovering
    noctalia.setUpdateInterval(16)
    update()
end

function onClick()
    noctalia.runAsync('"$HOME/.local/bin/classes" pin')
end

function onIpc(event)
    if event == "update" then poll() end
end

barWidget.setGlyph("calendar")
barWidget.setGlyphColor("#88c0d0")
barWidget.setVisible(true)
barWidget.setText("")
noctalia.setUpdateInterval(1000)
poll()

function onRightClick()
    noctalia.runAsync('"$HOME/.local/bin/classes" reload')
end
