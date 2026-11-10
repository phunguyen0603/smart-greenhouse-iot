#ifndef __WEBSERVER_TASK_H__
#define __WEBSERVER_TASK_H__

#include <Arduino.h>

void setup_webserver();
void webserver_task(void *pvParameters);

#endif // __WEBSERVER_TASK_H__
