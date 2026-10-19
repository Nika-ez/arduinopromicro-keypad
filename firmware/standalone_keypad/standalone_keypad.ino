#include <Keyboard.h>
#include <Adafruit_NeoPixel.h>
#include <EEPROM.h>
#include <avr/wdt.h>

#define MAGIC 0x4B50
#define FW_VER 2
#define LED_COUNT 7
#define KEY_COUNT 7
#define LED_PIN 10
#define FRAME_MS 25
#define DB_MS 5

const uint8_t keyPins[KEY_COUNT] = { 2, 3, 4, 5, 6, 7, 8 };
const uint8_t ledToKey[LED_COUNT] = { 6, 0, 3, 2, 4, 5, 1 };
const uint8_t ledOfKey[KEY_COUNT] = { 1, 6, 3, 2, 4, 5, 0 };

const uint8_t neighbors[KEY_COUNT][4] = {
  { 1, 2, 3, 255 },
  { 0, 2, 4, 255 },
  { 0, 1, 3, 5 },
  { 0, 2, 6, 255 },
  { 1, 5, 255, 255 },
  { 2, 4, 6, 255 },
  { 3, 5, 255, 255 }
};

struct Config {
  uint16_t magic;
  uint8_t version;
  uint8_t led[LED_COUNT][3];
  uint8_t enableMask;
  uint8_t pressColor[3];
  uint8_t brightIdle;
  uint8_t brightPress;
  uint8_t pressFx;
  uint8_t idleFx;
  uint8_t speed;
  uint8_t surround;
  uint8_t surroundStrength;
  uint8_t keymap[KEY_COUNT];
  uint8_t chk;
};

Config cfg;
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

bool keyDown[KEY_COUNT];
bool rawLast[KEY_COUNT];
uint8_t sentKey[KEY_COUNT];
uint32_t dbAt[KEY_COUNT];

uint8_t level[LED_COUNT];
uint8_t spark[LED_COUNT];
uint32_t sparkAt = 0;
uint32_t rndState = 12345;
uint32_t lastFrame = 0;

char buf[64];
uint8_t bufLen = 0;

uint8_t cfgChk() {
  uint8_t c = 0;
  const uint8_t* p = (const uint8_t*)&cfg;
  for (uint16_t i = 0; i < sizeof(Config) - 1; i++) c ^= p[i];
  return c;
}

void cfgSave() {
  cfg.chk = cfgChk();
  const uint8_t* p = (const uint8_t*)&cfg;
  for (uint16_t i = 0; i < sizeof(Config); i++) EEPROM.update(i, p[i]);
}

void cfgDefaults() {
  cfg.magic = MAGIC;
  cfg.version = FW_VER;
  for (uint8_t i = 0; i < LED_COUNT; i++) {
    cfg.led[i][0] = 255;
    cfg.led[i][1] = 255;
    cfg.led[i][2] = 255;
  }
  cfg.enableMask = 0x7F;
  cfg.pressColor[0] = 255;
  cfg.pressColor[1] = 255;
  cfg.pressColor[2] = 255;
  cfg.brightIdle = 0;
  cfg.brightPress = 51;
  cfg.pressFx = 1;
  cfg.idleFx = 0;
  cfg.speed = 5;
  cfg.surround = 0;
  cfg.surroundStrength = 40;
  const uint8_t def[KEY_COUNT] = { 'w', 'a', 's', 'd', 0x81, 0x80, ' ' };
  for (uint8_t i = 0; i < KEY_COUNT; i++) cfg.keymap[i] = def[i];
}

void cfgLoad() {
  EEPROM.get(0, cfg);
  if (cfg.magic != MAGIC || cfg.version != FW_VER || cfg.chk != cfgChk()) {
    cfgDefaults();
    cfgSave();
  }
}

void prU8(uint8_t v) {
  char t[5];
  itoa(v, t, 10);
  Serial.print(t);
}

void ok(const char* t) {
  Serial.print(F("OK:"));
  Serial.println(t);
}

void err(const char* t) {
  Serial.print(F("ERR:"));
  Serial.println(t);
}

uint8_t cl8(char* s) {
  long v = atol(s);
  if (v < 0) v = 0;
  if (v > 255) v = 255;
  return (uint8_t)v;
}

uint32_t wheel(uint8_t pos) {
  if (pos < 85) return strip.Color(255 - pos * 3, pos * 3, 0);
  if (pos < 170) {
    pos -= 85;
    return strip.Color(0, 255 - pos * 3, pos * 3);
  }
  pos -= 170;
  return strip.Color(pos * 3, 0, 255 - pos * 3);
}

void sendGet() {
  for (uint8_t i = 0; i < LED_COUNT; i++) {
    Serial.print(F("LED:"));
    prU8(i);
    Serial.print(':');
    prU8(cfg.led[i][0]);
    Serial.print(':');
    prU8(cfg.led[i][1]);
    Serial.print(':');
    prU8(cfg.led[i][2]);
    Serial.print(':');
    Serial.println((cfg.enableMask >> i) & 1);
  }
  Serial.print(F("PRESS:"));
  prU8(cfg.pressColor[0]);
  Serial.print(':');
  prU8(cfg.pressColor[1]);
  Serial.print(':');
  Serial.println(cfg.pressColor[2]);
  Serial.print(F("BRIGHT:"));
  prU8(cfg.brightIdle);
  Serial.print(':');
  Serial.println(cfg.brightPress);
  Serial.print(F("FX:"));
  prU8(cfg.pressFx);
  Serial.print(':');
  prU8(cfg.idleFx);
  Serial.print(':');
  prU8(cfg.speed);
  Serial.print(':');
  prU8(cfg.surround);
  Serial.print(':');
  Serial.println(cfg.surroundStrength);
  for (uint8_t i = 0; i < KEY_COUNT; i++) {
    Serial.print(F("KEY:"));
    prU8(i);
    Serial.print(':');
    Serial.println(cfg.keymap[i]);
  }
  Serial.println(F("END"));
}

void handleLine(char* s) {
  char* t = strtok(s, ": ");
  if (!t) return;
  if (!strcmp(t, "PING")) {
    Serial.println(F("PONG"));
    return;
  }
  if (!strcmp(t, "ID")) {
    Serial.print(F("ID:STANDALONE_KEYPAD:"));
    Serial.println(FW_VER);
    return;
  }
  if (!strcmp(t, "GET")) {
    sendGet();
    return;
  }
  if (!strcmp(t, "RESET")) {
    cfgDefaults();
    cfgSave();
    ok("RESET");
    return;
  }
  if (!strcmp(t, "REBOOT")) {
    ok("REBOOT");
    delay(80);
    wdt_enable(WDTO_15MS);
    while (1) {}
  }
  if (!strcmp(t, "SET")) {
    char* sub = strtok(NULL, ": ");
    if (!sub) {
      err("ARGS");
      return;
    }
    if (!strcmp(sub, "LED")) {
      char* a = strtok(NULL, ": ");
      char* b = strtok(NULL, ": ");
      char* c = strtok(NULL, ": ");
      char* d = strtok(NULL, ": ");
      if (!a || !b || !c || !d) {
        err("ARGS");
        return;
      }
      uint8_t i = cl8(a), r = cl8(b), g = cl8(c), bl = cl8(d);
      if (i == 255) {
        for (uint8_t k = 0; k < LED_COUNT; k++) {
          cfg.led[k][0] = r;
          cfg.led[k][1] = g;
          cfg.led[k][2] = bl;
        }
      } else if (i < LED_COUNT) {
        cfg.led[i][0] = r;
        cfg.led[i][1] = g;
        cfg.led[i][2] = bl;
      } else {
        err("RANGE");
        return;
      }
      cfgSave();
      ok("LED");
      return;
    }
    if (!strcmp(sub, "ENA")) {
      char* a = strtok(NULL, ": ");
      char* b = strtok(NULL, ": ");
      if (!a || !b) {
        err("ARGS");
        return;
      }
      uint8_t i = cl8(a), e = cl8(b) ? 1 : 0;
      if (i == 255) {
        cfg.enableMask = e ? 0x7F : 0;
      } else if (i < LED_COUNT) {
        if (e) cfg.enableMask |= (1 << i);
        else cfg.enableMask &= ~(1 << i);
      } else {
        err("RANGE");
        return;
      }
      cfgSave();
      ok("ENA");
      return;
    }
    if (!strcmp(sub, "PRESS")) {
      char* a = strtok(NULL, ": ");
      char* b = strtok(NULL, ": ");
      char* c = strtok(NULL, ": ");
      if (!a || !b || !c) {
        err("ARGS");
        return;
      }
      cfg.pressColor[0] = cl8(a);
      cfg.pressColor[1] = cl8(b);
      cfg.pressColor[2] = cl8(c);
      cfgSave();
      ok("PRESS");
      return;
    }
    if (!strcmp(sub, "BRIGHT")) {
      char* a = strtok(NULL, ": ");
      char* b = strtok(NULL, ": ");
      if (!a || !b) {
        err("ARGS");
        return;
      }
      cfg.brightIdle = cl8(a);
      cfg.brightPress = cl8(b);
      cfgSave();
      ok("BRIGHT");
      return;
    }
    if (!strcmp(sub, "FX")) {
      char* a = strtok(NULL, ": ");
      char* b = strtok(NULL, ": ");
      char* c = strtok(NULL, ": ");
      char* d = strtok(NULL, ": ");
      char* e = strtok(NULL, ": ");
      if (!a || !b || !c || !d || !e) {
        err("ARGS");
        return;
      }
      cfg.pressFx = cl8(a);
      cfg.idleFx = cl8(b);
      cfg.speed = cl8(c);
      cfg.surround = cl8(d) ? 1 : 0;
      cfg.surroundStrength = cl8(e);
      cfgSave();
      ok("FX");
      return;
    }
    if (!strcmp(sub, "KEY")) {
      char* a = strtok(NULL, ": ");
      char* b = strtok(NULL, ": ");
      if (!a || !b) {
        err("ARGS");
        return;
      }
      uint8_t i = cl8(a);
      if (i >= KEY_COUNT) {
        err("RANGE");
        return;
      }
      cfg.keymap[i] = cl8(b);
      cfgSave();
      ok("KEY");
      return;
    }
    err("SUB");
    return;
  }
  err("CMD");
}

void readSerial() {
  while (Serial.available()) {
    char ch = (char)Serial.read();
    if (ch == '\n' || ch == '\r') {
      if (bufLen) {
        buf[bufLen] = 0;
        handleLine(buf);
        bufLen = 0;
      }
    } else if (bufLen < 63) {
      buf[bufLen++] = ch;
    }
  }
}

uint8_t kscale(uint8_t k, uint16_t spd) {
  uint16_t v = (uint16_t)k * (11 - spd) / 6;
  if (v < 1) v = 1;
  return (uint8_t)v;
}

uint8_t idleTarget(uint8_t c, uint32_t now, uint16_t spd) {
  if (cfg.idleFx == 0) return 0;
  if (cfg.idleFx == 2) {
    uint16_t per = 4400 - spd * 240;
    uint16_t t = now % per;
    uint16_t tri = (t < per / 2) ? (uint16_t)((uint32_t)t * 510 / per) : (uint16_t)((uint32_t)(per - t) * 510 / per);
    return (uint16_t)cfg.brightIdle * (35 + tri * 65 / 255) / 100;
  }
  if (cfg.idleFx == 4) {
    uint16_t ph = (now / 6 + (uint16_t)c * 36) & 255;
    uint16_t tri = ph < 128 ? ph * 2 : (255 - ph) * 2;
    return (uint16_t)cfg.brightIdle * (30 + tri * 70 / 255) / 100;
  }
  return cfg.brightIdle;
}

void colForIdle(uint8_t c, uint32_t now, uint8_t* r, uint8_t* g, uint8_t* b) {
  if (cfg.idleFx == 3) {
    uint32_t w = wheel((uint8_t)(now / 20 + (uint16_t)c * 36));
    *r = (w >> 16) & 255;
    *g = (w >> 8) & 255;
    *b = w & 255;
    return;
  }
  *r = cfg.led[c][0];
  *g = cfg.led[c][1];
  *b = cfg.led[c][2];
}

void renderFrame(uint32_t now) {
  uint16_t spd = cfg.speed < 1 ? 1 : (cfg.speed > 10 ? 10 : cfg.speed);

  bool litp[LED_COUNT];
  bool glow[LED_COUNT];
  for (uint8_t c = 0; c < LED_COUNT; c++) {
    uint8_t k = ledToKey[c];
    litp[c] = keyDown[k];
    glow[c] = false;
    if (cfg.surround && !litp[c]) {
      for (uint8_t n = 0; n < 4; n++) {
        uint8_t nb = neighbors[k][n];
        if (nb == 255) break;
        if (keyDown[nb]) {
          glow[c] = true;
          break;
        }
      }
    }
  }

  if (cfg.idleFx == 5 && now - sparkAt > (uint32_t)(900 - spd * 60)) {
    sparkAt = now;
    rndState = rndState * 1664525 + 1013904223;
    uint8_t c = (uint8_t)(rndState >> 24) % LED_COUNT;
    spark[c] = 255;
  }

  uint8_t kUp, kDn;
  if (cfg.pressFx == 0) {
    kUp = 1;
    kDn = 1;
  } else if (cfg.pressFx == 1) {
    kUp = 1;
    kDn = kscale(3, spd);
  } else if (cfg.pressFx == 2) {
    kUp = kscale(6, spd);
    kDn = kscale(9, spd);
  } else {
    kUp = kscale(2, spd);
    kDn = kscale(2, spd);
  }

  for (uint8_t c = 0; c < LED_COUNT; c++) {
    uint8_t target;
    if (litp[c]) target = cfg.brightPress;
    else if (glow[c]) target = (uint16_t)cfg.brightPress * cfg.surroundStrength / 100;
    else target = idleTarget(c, now, spd);

    int16_t d = (int16_t)target - (int16_t)level[c];
    if (d != 0) {
      int16_t step = d / (d > 0 ? kUp : kDn);
      if (step == 0) step = (d > 0) ? 1 : -1;
      level[c] = (uint8_t)((int16_t)level[c] + step);
    }

    uint8_t outLv = level[c];
    uint8_t colR, colG, colB;
    if (litp[c] || glow[c]) {
      colR = cfg.pressColor[0];
      colG = cfg.pressColor[1];
      colB = cfg.pressColor[2];
    } else {
      colForIdle(c, now, &colR, &colG, &colB);
    }

    if (spark[c] > 0) {
      if (!litp[c] && !glow[c]) {
        uint8_t sl = (uint16_t)spark[c] * cfg.brightPress / 255;
        if (sl > outLv) {
          outLv = sl;
          colR = 255;
          colG = 255;
          colB = 255;
        }
      }
      spark[c] = spark[c] > 14 ? spark[c] - 14 : 0;
    }

    if (!((cfg.enableMask >> c) & 1)) {
      strip.setPixelColor(c, 0, 0, 0);
      continue;
    }
    uint8_t r = (uint16_t)colR * outLv / 255;
    uint8_t g = (uint16_t)colG * outLv / 255;
    uint8_t b = (uint16_t)colB * outLv / 255;
    strip.setPixelColor(c, r, g, b);
  }
  strip.show();
}

void scanKeys(uint32_t now) {
  for (uint8_t i = 0; i < KEY_COUNT; i++) {
    bool rd = digitalRead(keyPins[i]);
    if (rd != rawLast[i]) {
      dbAt[i] = now;
      rawLast[i] = rd;
      continue;
    }
    if (now - dbAt[i] < DB_MS) continue;
    bool dn = !rd;
    if (dn == keyDown[i]) continue;
    keyDown[i] = dn;
    if (dn) {
      sentKey[i] = cfg.keymap[i];
      Keyboard.press(sentKey[i]);
      if (cfg.pressFx == 3) {
        uint16_t ov = (uint16_t)cfg.brightPress * 130 / 100;
        if (ov > 255) ov = 255;
        level[ledOfKey[i]] = (uint8_t)ov;
      }
    } else {
      Keyboard.release(sentKey[i]);
    }
    Serial.print(F("EVT:"));
    prU8(i);
    Serial.print(':');
    Serial.println(dn ? 1 : 0);
  }
}

void setup() {
  for (uint8_t i = 0; i < KEY_COUNT; i++) {
    pinMode(keyPins[i], INPUT_PULLUP);
    rawLast[i] = HIGH;
  }
  Serial.begin(115200);
  strip.begin();
  strip.show();
  cfgLoad();
  Keyboard.begin();
}

void loop() {
  uint32_t now = millis();
  readSerial();
  scanKeys(now);
  if (now - lastFrame >= FRAME_MS) {
    lastFrame = now;
    renderFrame(now);
  }
}
