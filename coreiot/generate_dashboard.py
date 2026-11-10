import uuid
import json

def generate_valid_dashboard():
    def make_id():
        return str(uuid.uuid4())

    alias_id = make_id()
    w_temp_id = make_id()
    w_humi_id = make_id()
    w_vpd_id = make_id()
    w_ai_id = make_id()
    w_fan_id = make_id()
    w_pump_id = make_id()
    w_chart_id = make_id()

    dashboard_data = {
        "title": "Smart Greenhouse Climate Dashboard (HK261)",
        "image": None,
        "mobileHide": False,
        "mobileOrder": None,
        "configuration": {
            "description": "Smart Greenhouse Real-Time Monitoring & Edge AI (HK261)",
            "widgets": {
                w_temp_id: {
                    "isSystemType": True,
                    "bundleAlias": "cards",
                    "typeAlias": "value_card",
                    "type": "latest",
                    "title": "Nhiệt độ (°C)",
                    "image": None,
                    "description": None,
                    "sizeX": 6,
                    "sizeY": 4,
                    "config": {
                        "datasources": [
                            {
                                "type": "entity",
                                "entityAliasId": alias_id,
                                "dataKeys": [
                                    {
                                        "name": "temperature",
                                        "type": "timeseries",
                                        "label": "Nhiệt độ",
                                        "color": "#e65100",
                                        "settings": {}
                                    }
                                ]
                            }
                        ],
                        "showTitle": True,
                        "title": "Nhiệt độ (°C)",
                        "dropShadow": True,
                        "enableFullscreen": True,
                        "settings": {
                            "units": "°C",
                            "decimals": 1
                        }
                    }
                },
                w_humi_id: {
                    "isSystemType": True,
                    "bundleAlias": "cards",
                    "typeAlias": "value_card",
                    "type": "latest",
                    "title": "Độ ẩm (%)",
                    "image": None,
                    "description": None,
                    "sizeX": 6,
                    "sizeY": 4,
                    "config": {
                        "datasources": [
                            {
                                "type": "entity",
                                "entityAliasId": alias_id,
                                "dataKeys": [
                                    {
                                        "name": "humidity",
                                        "type": "timeseries",
                                        "label": "Độ ẩm",
                                        "color": "#0288d1",
                                        "settings": {}
                                    }
                                ]
                            }
                        ],
                        "showTitle": True,
                        "title": "Độ ẩm (%)",
                        "dropShadow": True,
                        "enableFullscreen": True,
                        "settings": {
                            "units": "%",
                            "decimals": 1
                        }
                    }
                },
                w_vpd_id: {
                    "isSystemType": True,
                    "bundleAlias": "cards",
                    "typeAlias": "value_card",
                    "type": "latest",
                    "title": "Độ hụt áp suất hơi (VPD)",
                    "image": None,
                    "description": None,
                    "sizeX": 6,
                    "sizeY": 4,
                    "config": {
                        "datasources": [
                            {
                                "type": "entity",
                                "entityAliasId": alias_id,
                                "dataKeys": [
                                    {
                                        "name": "vpd",
                                        "type": "timeseries",
                                        "label": "VPD",
                                        "color": "#2e7d32",
                                        "settings": {}
                                    }
                                ]
                            }
                        ],
                        "showTitle": True,
                        "title": "VPD (kPa)",
                        "dropShadow": True,
                        "enableFullscreen": True,
                        "settings": {
                            "units": "kPa",
                            "decimals": 2
                        }
                    }
                },
                w_ai_id: {
                    "isSystemType": True,
                    "bundleAlias": "cards",
                    "typeAlias": "latest_values",
                    "type": "latest",
                    "title": "Trạng thái Edge AI (TinyML)",
                    "image": None,
                    "description": None,
                    "sizeX": 6,
                    "sizeY": 4,
                    "config": {
                        "datasources": [
                            {
                                "type": "entity",
                                "entityAliasId": alias_id,
                                "dataKeys": [
                                    {
                                        "name": "tinyml_state_str",
                                        "type": "timeseries",
                                        "label": "Trạng thái AI",
                                        "color": "#6a1b9a",
                                        "settings": {}
                                    },
                                    {
                                        "name": "tinyml_confidence",
                                        "type": "timeseries",
                                        "label": "Độ tin cậy",
                                        "color": "#43a047",
                                        "settings": {}
                                    }
                                ]
                            }
                        ],
                        "showTitle": True,
                        "title": "Trạng thái Edge AI",
                        "dropShadow": True,
                        "enableFullscreen": True,
                        "settings": {}
                    }
                },
                w_fan_id: {
                    "isSystemType": True,
                    "bundleAlias": "control_widgets",
                    "typeAlias": "round_switch",
                    "type": "rpc",
                    "title": "Công tắc Quạt thông gió",
                    "image": None,
                    "description": None,
                    "sizeX": 6,
                    "sizeY": 4,
                    "config": {
                        "targetDevice": {
                            "type": "entity",
                            "entityAliasId": alias_id
                        },
                        "showTitle": True,
                        "title": "Quạt thông gió (FAN)",
                        "dropShadow": True,
                        "enableFullscreen": True,
                        "settings": {
                            "initialValueMethod": "getStateFAN",
                            "methodParams": "",
                            "parseValueFunction": "return data ? true : false;",
                            "retrieveValueMethod": "getStateFAN",
                            "setValueMethod": "setStateFAN",
                            "requestTimeout": 5000,
                            "switchTitle": "Quạt thông gió"
                        }
                    }
                },
                w_pump_id: {
                    "isSystemType": True,
                    "bundleAlias": "control_widgets",
                    "typeAlias": "round_switch",
                    "type": "rpc",
                    "title": "Công tắc Máy phun sương",
                    "image": None,
                    "description": None,
                    "sizeX": 6,
                    "sizeY": 4,
                    "config": {
                        "targetDevice": {
                            "type": "entity",
                            "entityAliasId": alias_id
                        },
                        "showTitle": True,
                        "title": "Phun sương (PUMP)",
                        "dropShadow": True,
                        "enableFullscreen": True,
                        "settings": {
                            "initialValueMethod": "getStatePUMP",
                            "methodParams": "",
                            "parseValueFunction": "return data ? true : false;",
                            "retrieveValueMethod": "getStatePUMP",
                            "setValueMethod": "setStatePUMP",
                            "requestTimeout": 5000,
                            "switchTitle": "Máy phun sương"
                        }
                    }
                },
                w_chart_id: {
                    "isSystemType": True,
                    "bundleAlias": "charts",
                    "typeAlias": "timeseries",
                    "type": "timeseries",
                    "title": "Biểu đồ Chuỗi thời gian Vi khí hậu & Dự báo AI",
                    "image": None,
                    "description": None,
                    "sizeX": 12,
                    "sizeY": 6,
                    "config": {
                        "datasources": [
                            {
                                "type": "entity",
                                "entityAliasId": alias_id,
                                "dataKeys": [
                                    {
                                        "name": "temperature",
                                        "type": "timeseries",
                                        "label": "Nhiệt độ (°C)",
                                        "color": "#e65100",
                                        "settings": {}
                                    },
                                    {
                                        "name": "humidity",
                                        "type": "timeseries",
                                        "label": "Độ ẩm (%)",
                                        "color": "#0288d1",
                                        "settings": {}
                                    },
                                    {
                                        "name": "predicted_temp_60m",
                                        "type": "timeseries",
                                        "label": "Dự báo (+60m)",
                                        "color": "#d81b60",
                                        "settings": {}
                                    }
                                ]
                            }
                        ],
                        "showTitle": True,
                        "title": "Biểu đồ Vi khí hậu & Dự báo AI (+60 phút)",
                        "dropShadow": True,
                        "enableFullscreen": True,
                        "settings": {
                            "stack": False,
                            "fontSize": 10
                        }
                    }
                }
            },
            "states": {
                "default": {
                    "name": "Smart Greenhouse Climate Dashboard (HK261)",
                    "root": True,
                    "layouts": {
                        "main": {
                            "widgets": {
                                w_temp_id:  {"sizeX": 6,  "sizeY": 4, "row": 0, "col": 0},
                                w_humi_id:  {"sizeX": 6,  "sizeY": 4, "row": 0, "col": 6},
                                w_vpd_id:   {"sizeX": 6,  "sizeY": 4, "row": 0, "col": 12},
                                w_ai_id:    {"sizeX": 6,  "sizeY": 4, "row": 0, "col": 18},
                                w_fan_id:   {"sizeX": 6,  "sizeY": 4, "row": 4, "col": 0},
                                w_pump_id:  {"sizeX": 6,  "sizeY": 4, "row": 4, "col": 6},
                                w_chart_id: {"sizeX": 12, "sizeY": 6, "row": 4, "col": 12}
                            },
                            "gridSettings": {
                                "backgroundColor": "#f8f9fa",
                                "columns": 24,
                                "margin": 10,
                                "outerMargin": True
                            }
                        }
                    }
                }
            },
            "entityAliases": {
                alias_id: {
                    "id": alias_id,
                    "alias": "GreenhouseDevice",
                    "filter": {
                        "type": "entityType",
                        "entityType": "DEVICE",
                        "resolveMultiple": False
                    }
                }
            },
            "timewindow": {
                "displayValue": "",
                "hideInterval": False,
                "hideAggregation": False,
                "hideAggInterval": False,
                "hideTimezone": False,
                "selectedTab": 0,
                "realtime": {
                    "realtimeType": 0,
                    "interval": 1000,
                    "timewindowMs": 60000
                },
                "aggregation": {
                    "type": "NONE",
                    "limit": 25000
                }
            },
            "settings": {
                "stateControllerId": "entity",
                "showTitle": False,
                "showDashboardsSelect": True,
                "showEntitiesSelect": True,
                "showDashboardTimewindow": True,
                "showDashboardExport": True,
                "toolbarAlwaysOpen": True
            }
        }
    }

    with open(r"d:\BK\HK261\IoT\Assignment\coreiot\dashboard_greenhouse.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
    print("dashboard_greenhouse.json generated successfully with valid layout & widgets!")

if __name__ == "__main__":
    generate_valid_dashboard()
