/**
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {Terminal} from 'xterm';
import {FitAddon} from 'xterm-addon-fit';
import {WebLinksAddon} from 'xterm-addon-web-links';
import axios, {AxiosResponse, AxiosError} from 'axios';
import {io, Socket} from 'socket.io-client';
import 'xterm/css/xterm.css';

interface RxDataNotifyPayload {
  'data': {
    'room': string;
    'rx_data': string;
  };
}

interface TxDataNotifyPayload {
  'data': {
    'room':string;
    'tx_data':string;
    'from':string;
  };
}
interface ServerToClientEvents {
  join_response: (data:any) => void;
  rx_data_notify: (data:RxDataNotifyPayload) => void;
  tx_data_notify: (data:TxDataNotifyPayload) => void;
}

interface JoinRequestPayload {
  'room':string;
  'client':string;
}

interface LeaveRequestPayload {
  'room':string;
}

interface SendDataRequestPayload {
  'room':string;
  'tx_data':string;
}

/*
interface GetPortStatusResponse {
  'name':string;
  'is_open':boolean;
  'baudrate':number;
  'bytesize':number;
  'parity':string;
  'stopbits':number;
  'timeout':number | undefined;
  'write_timeout':number | undefined;
  'inter_byte_timeout':number | undefined;
  'xonxoff':boolean;
  'rtscts':boolean;
  'dsrdtr':boolean;
  'rts':boolean;
  'dtr':boolean;
  'cts':boolean | undefined;
  'dts':boolean | undefined;
  'ri':boolean | undefined;
  'cd':boolean | undefined;
}
*/

interface GetPortResponse {
  'device':string;
  'name': string;
  'description': string | undefined;
  'hwid': string | undefined;
  'vid': number | undefined;
  'pid': number | undefined;
  'serial_number': string | undefined;
  'location': string | undefined;
  'manufacturer': string | undefined;
  'product': string | undefined;
  'interface': string | undefined;
}
interface ClientToServerEvents {
  join: (arg0:JoinRequestPayload) => void;
  leave: (arg0:LeaveRequestPayload) => void;
  send_data: (arg0:SendDataRequestPayload) => void;
}

/**
 * Elements of the port selection dropdown extend HTMLOptionElement so that
 * they can reference the SerialPort they represent.
 */
declare class PortOption extends HTMLOptionElement {
  port: string;
}

let portSelector: HTMLSelectElement;
let connectButton: HTMLButtonElement;
let baudRateSelector: HTMLSelectElement;
let customBaudRateInput: HTMLInputElement;
let dataBitsSelector: HTMLSelectElement;
let paritySelector: HTMLSelectElement;
let stopBitsSelector: HTMLSelectElement;
let flowControlCheckbox: HTMLInputElement;
let echoCheckbox: HTMLInputElement;

let socket: Socket<ServerToClientEvents, ClientToServerEvents>;

let port: string | undefined;

const bufferSize = 8 * 1024; // 8kB

const term = new Terminal({
  scrollback: 10_000,
});

const fitAddon = new FitAddon();
term.loadAddon(fitAddon);

term.loadAddon(new WebLinksAddon());

let toFlush = '';
term.onData((data) => {
  if (port) {
    if (echoCheckbox.checked) {
      term.write(data);
      if (data === '\r') {
        term.writeln('');
      }
    }
    if (data === '\r') {
      // const txData = encoder.encode(toFlush);
      socket.emit('send_data', {room: port, tx_data: toFlush});
      toFlush = '';
    } else {
      toFlush += data;
    }
  }
});

/**
 * Adds the given port to the selection dropdown.
 *
 * @param {SerialPort} port the port to add
 * @return {PortOption}
 */
function addNewPort(port: GetPortResponse): PortOption {
  const portOption = document.createElement('option') as PortOption;
  portOption.textContent = `${port.name} : ${port.description}`;
  portOption.port = port.device;
  portSelector.appendChild(portOption);
  return portOption;
}

/**
 * Download the terminal's contents to a file.
 */
function downloadTerminalContents(): void {
  if (!term) {
    throw new Error('no terminal instance found');
  }

  if (term.rows === 0) {
    console.log('No output yet');
    return;
  }

  term.selectAll();
  const contents = term.getSelection();
  term.clearSelection();
  const linkContent = URL.createObjectURL(
      new Blob([new TextEncoder().encode(contents).buffer],
          {type: 'text/plain'}));
  const fauxLink = document.createElement('a');
  fauxLink.download = `terminal_content_${new Date().getTime()}.txt`;
  fauxLink.href = linkContent;
  fauxLink.click();
}

/**
 * Clear the terminal's contents.
 */
function clearTerminalContents(): void {
  if (!term) {
    throw new Error('no terminal instance found');
  }

  if (term.rows === 0) {
    console.log('No output yet');
    return;
  }

  term.clear();
}

/**
 * Sets |port| to the currently selected port. If none is selected then the
 * user is prompted for one.
 */
async function getSelectedPort(): Promise<void> {
  const selectedOption = portSelector.selectedOptions[0] as PortOption;
  port = selectedOption.port;
}

/**
 * @return {number} the currently selected baud rate
 */
function getSelectedBaudRate(): number {
  if (baudRateSelector.value == 'custom') {
    return Number.parseInt(customBaudRateInput.value);
  }
  return Number.parseInt(baudRateSelector.value);
}

/**
 * Resets the UI back to the disconnected state.
 */
function markDisconnected(): void {
  term.writeln('<DISCONNECTED>');
  portSelector.disabled = false;
  connectButton.textContent = 'Connect';
  connectButton.disabled = false;
  baudRateSelector.disabled = false;
  customBaudRateInput.disabled = false;
  dataBitsSelector.disabled = false;
  paritySelector.disabled = false;
  stopBitsSelector.disabled = false;
  flowControlCheckbox.disabled = false;
  port = undefined;
}

/**
 * Initiates a connection to the selected port.
 */
async function connectToPort(): Promise<void> {
  await getSelectedPort();
  if (!port) {
    return;
  }

  const options = {
    baudRate: getSelectedBaudRate(),
    dataBits: Number.parseInt(dataBitsSelector.value),
    parity: paritySelector.value as ParityType,
    stopBits: Number.parseInt(stopBitsSelector.value),
    flowControl:
        flowControlCheckbox.checked ? <const> 'hardware' : <const> 'none',
    bufferSize,

    // Prior to Chrome 86 these names were used.
    baudrate: getSelectedBaudRate(),
    databits: Number.parseInt(dataBitsSelector.value),
    stopbits: Number.parseInt(stopBitsSelector.value),
    rtscts: flowControlCheckbox.checked,
  };
  console.log(port);
  console.log(options);

  portSelector.disabled = true;
  connectButton.textContent = 'Connecting...';
  connectButton.disabled = true;
  baudRateSelector.disabled = true;
  customBaudRateInput.disabled = true;
  dataBitsSelector.disabled = true;
  paritySelector.disabled = true;
  stopBitsSelector.disabled = true;
  flowControlCheckbox.disabled = true;

  if (socket.id) {
    await new Promise((resolve) => {
      if (port && socket.id) {
        socket.on('join_response', (data:any) => {
          socket.off('join_response');
          // console.log(data.data.rooms);
          const filteredRooms = data.data.rooms.filter((r:string)=>r === port);
          if (filteredRooms.length === 1) {
            socket.on('rx_data_notify', (data:RxDataNotifyPayload) => {
              (new Promise<void>((resolve) => {
                term.writeln(data.data.rx_data, resolve);
              }));
            });
            socket.on('tx_data_notify', (data:TxDataNotifyPayload) => {
              (new Promise<void>((resolve) => {
                term.writeln(data.data.tx_data, resolve);
              }));
            });
            term.writeln('<CONNECTED>');
            connectButton.textContent = 'Disconnect';
            connectButton.disabled = false;
            resolve(port);
          } else {
            markDisconnected();
            resolve(null);
          }
        });
        socket.emit('join', {room: port, client: socket.id});
      }
    });
  } else {
    markDisconnected();
  }
}

/**
 * Closes the currently active connection.
 */
async function disconnectFromPort(): Promise<void> {
  if (port) {
    socket.emit('leave', {room: port});
    socket.off('rx_data_notify');
    socket.off('tx_data_notify');
    markDisconnected();
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const terminalElement = document.getElementById('terminal');
  if (terminalElement) {
    term.open(terminalElement);
    fitAddon.fit();

    window.addEventListener('resize', () => {
      fitAddon.fit();
    });
  }

  const downloadOutput =
    document.getElementById('download') as HTMLSelectElement;
  downloadOutput.addEventListener('click', downloadTerminalContents);

  const clearOutput = document.getElementById('clear') as HTMLSelectElement;
  clearOutput.addEventListener('click', clearTerminalContents);

  portSelector = document.getElementById('ports') as HTMLSelectElement;

  connectButton = document.getElementById('connect') as HTMLButtonElement;
  connectButton.addEventListener('click', () => {
    if (port) {
      disconnectFromPort();
    } else {
      connectToPort();
    }
  });

  baudRateSelector = document.getElementById('baudrate') as HTMLSelectElement;
  baudRateSelector.addEventListener('input', () => {
    if (baudRateSelector.value == 'custom') {
      customBaudRateInput.hidden = false;
    } else {
      customBaudRateInput.hidden = true;
    }
  });

  customBaudRateInput =
      document.getElementById('custom_baudrate') as HTMLInputElement;
  dataBitsSelector = document.getElementById('databits') as HTMLSelectElement;
  paritySelector = document.getElementById('parity') as HTMLSelectElement;
  stopBitsSelector = document.getElementById('stopbits') as HTMLSelectElement;
  flowControlCheckbox = document.getElementById('rtscts') as HTMLInputElement;
  echoCheckbox = document.getElementById('echo') as HTMLInputElement;

  const convertEolCheckbox =
      document.getElementById('convert_eol') as HTMLInputElement;
  const convertEolCheckboxHandler = () => {
    term.options.convertEol = convertEolCheckbox.checked;
  };
  convertEolCheckbox.addEventListener('change', convertEolCheckboxHandler);
  convertEolCheckboxHandler();

  let portNumber = 5001;
  if (import.meta.env.MODE == 'development') {
    portNumber = 5001;
  }

  axios.get(`http://localhost:${portNumber}/ports`)
      .then((response:AxiosResponse)=>{
        Promise.all(response.data.map((port:string)=>axios.get(`http://localhost:${portNumber}/ports/${port}`)))
            .then((rsps:AxiosResponse[])=>{
              rsps.forEach((rsp) => addNewPort(rsp.data));
            })
            .catch((e: AxiosError<{ error: string }>)=>{
              console.log(e.message);
            });
      })
      .catch((e: AxiosError<{ error: string }>)=>{
        console.log(e.message);
      });

  try {
    socket = io(`http://localhost:${portNumber}/serialtransaction`, {
      reconnectionDelayMax: 10000,
    });
  } catch (e) {
    console.error(e);
  }
});
