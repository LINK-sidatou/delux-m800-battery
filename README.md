# DELUX M800 Ultra 电量托盘

Windows 任务栏托盘里实时显示 **DELUX（多彩）M800 Ultra** 无线鼠标的电量百分比，不依赖官方驱动，也不常驻后台大程序。

![icon preview](docs/icon-preview.png)

> 数字就是电量：>50% 绿色，20–50% 琥珀，≤20% 红色，充电中蓝色（底部加白条），未连接显示 `--`。

## 为什么需要它

这只鼠标走 2.4G 接收器连接时，Windows 系统层面**看不到任何电量信息**（系统只给蓝牙鼠标报电量），要看得开官方驱动。本工具直接读接收器的私有 HID 报文，一个托盘图标常驻显示，不用开驱动。

## 使用方法

1. 依赖（Python 3.10+）：

   ```bat
   python -m pip install hidapi pystray pillow
   ```

   > 注意：请装 `hidapi`（提供编译好的 `hid` 模块），**不要**装 PyPI 上纯 Python 的 `hid` 包，两者会冲突。

2. 双击 `启动托盘.vbs` 运行（无控制台窗口）。
3. 首次运行图标可能被 Windows 放进任务栏的 `^` 折叠区，把它拖到任务栏上即可常驻；或在「设置 → 个性化 → 任务栏 → 其他系统托盘图标」里打开。

右键托盘图标：

- **立即刷新**（双击图标同样是刷新）
- **刷新间隔**：30 秒 / 1 分钟 / 5 分钟
- **开机自启**：勾选后会把 `启动托盘.vbs` 复制到当前用户的 Startup 文件夹
- **退出**

电量 ≤15% 且未充电时，会弹一条系统通知。

也可以不进托盘，直接命令行取一次读数：

```bat
python mouse_battery.py
:: {'online': True, 'level': 72, 'charging': False}
```

## 逆向出来的协议

设备：`DELUX Receiver`，`VID 0x320F` / `PID 0x225B`，厂商 HID 集合 `usage_page 0xFF1C` / `usage 0x92`，`report id 4`，输入输出各 63 字节。

报文结构：

```
[report_id=0x04][crc16(2B)][cmd(1B)][block_len(1B)][block_off(1B)][data...]
```

- 接收器**不校验** crc16，发送时填 `00 00` 即可
- 未知命令的应答是 `04 ed 5a 00 00 00 00 ff`（`cmd = 0x00`，即「不支持」）
- 官方驱动会周期性发 `cmd = 0xaa` 保活帧，解析回包时必须按命令字过滤

### 查询电量

```
发送：04 00 00 1a 00 00 00 00 ...（其余补 0，共 64 字节）
回包：04 00 00 1a 00 00 00 ff | level | charging
```

| 偏移 | 含义 |
| --- | --- |
| 3 | 命令字 `0x1a` |
| 8 | 电量百分比 0–100 |
| 9 | bit0 = 充电中（插线充电时为 1） |

实测：插线升级固件时读到 `99 + 0x01`，拔线后为 `72 + 0x00`，与官方驱动的显示一致。关闭官方驱动后依然可读——协议是接收器直接应答的，与 `DELUX-M800Ultra.exe` 无关。

### 其他已知命令（读配置用，非本项目所需）

驱动初始化时会连发一组读命令，回包同样是上面的结构：

| cmd | 含义（推测） |
| --- | --- |
| `0x01` | 设备基本状态 |
| `0x02` | 设备信息 |
| `0x03` | 读块（`block_off` 为偏移） |
| `0x05` | 读块（24 字节一片，偏移 0/24/48/72） |
| `0x07` | 读块（按键/宏配置） |

## 已知问题

- 只测过 M800 Ultra（0x320F:0x225B）这一版接收器，其他多彩型号的协议大概率不同，不能直接用。
- 没测过有线模式和蓝牙模式：有线模式下设备可能以另一个 PID 出现，理论上命令相同（官方驱动也支持有线），但未验证；蓝牙模式下没有这条私有通道，系统原生就能显示电量。
- `pystray` 在无窗口（`pythonw`）方式启动时偶发静默退出，程序会把异常写进 `error.log`，遇到问题请带上这个文件反馈。

## 参考

同类项目的协议各不相同，仅作思路参考：

- [Colgate13/m900_pro_delux_drive](https://github.com/Colgate13/m900_pro_delux_drive)
- [coderlife-book/delux-m900-pro-battery](https://github.com/coderlife-book/delux-m900-pro-battery)
- [HHHHHH233333/2.4G-battery-viewer](https://github.com/HHHHHH233333/2.4G-battery-viewer)

## License

MIT
