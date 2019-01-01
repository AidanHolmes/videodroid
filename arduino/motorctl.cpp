/*
Serial command processor for motor controller
*/
#include <Arduino.h>
#include "command.hpp"

// States are a bit redundant. Code only cares about none or other state
//enum States {none, stop, lstop, rstop, lfwd,rfwd,lback,rback,fwd,back,standby} ;
enum States {cmd, pwm};
States state = cmd ;
const char *lastcmd = "";

// Pin configuration for Video Droid
const int pin_pwma = 5;
const int pin_ain1 = 2;
const int pin_ain2 = 4;
const int pin_pwmb = 6;
const int pin_bin1 = 7;
const int pin_bin2 = 8;
const int pin_standby = 11;

void callback_standby(int n)
{
  Serial.print("Standby command recevied\r\n");
  digitalWrite(pin_standby, LOW);
}

void callback_stop(int n)
{
  Serial.print("Stop command recevied: ");
  Serial.print(n);
  Serial.print("\r\n") ;
  digitalWrite(pin_ain1, HIGH);
  digitalWrite(pin_ain2, HIGH);
  digitalWrite(pin_bin1, HIGH);
  digitalWrite(pin_bin2, HIGH);
  analogWrite(pin_pwma, 0);
  analogWrite(pin_pwmb, 0);
}
void callback_lstop(int n)
{
  digitalWrite(pin_ain1, HIGH);
  digitalWrite(pin_ain2, HIGH);
  analogWrite(pin_pwma, 0);
}
void callback_rstop(int n)
{
  digitalWrite(pin_bin1, HIGH);
  digitalWrite(pin_bin2, HIGH);
  analogWrite(pin_pwmb, 0);
}
void callback_lfwd(int n){}
void callback_rfwd(int n){}
void callback_lback(int n){}
void callback_rback(int n){}
void callback_fwd(int n)
{
  Serial.print("Forward command received: ") ;
  Serial.print(n);
  Serial.print("\r\n");
  digitalWrite(pin_standby, HIGH);
  digitalWrite(pin_ain1, HIGH);
  digitalWrite(pin_ain2, LOW);
  digitalWrite(pin_bin1, HIGH);
  digitalWrite(pin_bin2, LOW);
  analogWrite(pin_pwma, n);
  analogWrite(pin_pwmb, n);
}
void callback_back(int n){}
void callback_lastcmd(int n)
{
  Serial.println(lastcmd);
}

// Last Command
Command cmd_lastcmd("cmd", &callback_lastcmd) ;
// Standby
Command cmd_standby("standby", &callback_standby) ;
// All stop
Command cmd_stop("stop", &callback_stop) ;
// left track stop
Command cmd_left_stop("lstop", &callback_lstop) ;
// right track stop
Command cmd_right_stop("rstop", &callback_rstop) ;
// left track forward
Command cmd_left_fwd("lfwd", &callback_lfwd) ;
// right track forward
Command cmd_right_fwd("rfwd", &callback_rfwd) ;
// left track backward
Command cmd_left_back("lback", &callback_lback) ;
// right track backward
Command cmd_right_back("rback", &callback_rback) ;
// All forward
Command cmd_forward("fwd", &callback_fwd) ;
// All backwards
Command cmd_backwards("back", &callback_back) ;

Command *active_cmds[] = {&cmd_lastcmd, &cmd_stop, &cmd_left_stop, &cmd_right_stop, &cmd_left_fwd, &cmd_right_fwd,
			  &cmd_left_back, &cmd_right_back, &cmd_forward, &cmd_backwards, &cmd_standby, NULL};

const int max_pwm_val = 4;
char pwmval[max_pwm_val];
int pwm_pos = 0;
Command *foundcmd = NULL ;

void reset_cmd_parser()
{
  pwmval[0] = '2';
  pwmval[1] = '5';
  pwmval[2] = '5';
  pwmval[3] = '\0';
  state = cmd ;
  pwm_pos = 0;
  foundcmd = NULL;
  digitalWrite(LED_BUILTIN, LOW);
}

void setup()
{
  Serial.begin(9600);
  while (!Serial);

  pinMode(LED_BUILTIN, OUTPUT);
  reset_cmd_parser();

  // Setup pins
  pinMode(pin_pwma, OUTPUT);
  pinMode(pin_ain1, OUTPUT);
  pinMode(pin_ain2, OUTPUT);
  pinMode(pin_pwmb, OUTPUT);
  pinMode(pin_bin1, OUTPUT);
  pinMode(pin_bin2, OUTPUT);
  pinMode(pin_standby, OUTPUT);  
}

void loop()
{
  int c, val ;
  Command **p ;
  
  if (Serial.available()){
    // Data in serial buffer
    c = Serial.read();
    
    switch(c){
    case ' ':
      if (state == cmd && foundcmd && foundcmd->found()){
	state = pwm;
      }
      break;
    case '\r':
    case '\n':
      if (foundcmd && foundcmd == &cmd_lastcmd){
	// Special case, this command takes no parameter
	foundcmd->cmd(0) ;
      }else if (state == pwm){
	// command keyword found, read pwm value
	if (pwm_pos >= max_pwm_val -1) pwm_pos = max_pwm_val - 1;
	pwmval[pwm_pos] = '\0' ;
	val = 0;
	if (pwm_pos > 0) // if value read
	  val = atoi(pwmval) ; // convert to int

	if (foundcmd){ // should be non NULL, but check anyway
	  foundcmd->cmd(val);
	  if (foundcmd != &cmd_lastcmd) // Only record last cmds which are not the last cmd query
	    lastcmd = foundcmd->name();
	}
      }
      
      // Reset all command searches
      for (p=active_cmds;*p;p++){
	(*p)->reset() ;
      }
      
      // reset command parser
      reset_cmd_parser();
      break;
    default:
      // normalise to lower case
      if (state == cmd){
	if (c >= 'A' && c <= 'Z'){
	 c -= 'A' - 'a';
	}

	if ((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ){
	  for (p=active_cmds;*p;p++){
	    if ((*p)->found(c)){
	      // Found a command. Note that more than one may match
	      digitalWrite(LED_BUILTIN, HIGH);
	      foundcmd = *p ;
	    }else if (foundcmd == *p){
	      // command no longer found, reset
	      digitalWrite(LED_BUILTIN, LOW);
	      foundcmd = NULL;
	    }
	  }
	}
      }else if (state == pwm){
	// Changed state. Look for number
	if (isDigit(c)){
	  // Write to pwm value buffer
	  if (pwm_pos >= max_pwm_val - 1) pwmval[max_pwm_val-1] = '\0' ;
	  else{
	    pwmval[pwm_pos++] = c ;
	  }
	}else{
	  // Nonsense
	  reset_cmd_parser();
	}
      }
    }
  }
}
