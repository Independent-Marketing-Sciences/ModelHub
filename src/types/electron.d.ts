export interface IElectronAPI {
  openFile: () => Promise<string | null>;
  readFile: (filePath: string) => Promise<string>;
  saveFile: (data: any) => Promise<string | null>;
  getAppVersion: () => Promise<string>;
  invoke: (channel: string, ...args: any[]) => Promise<any>;
}

export interface PythonBackendStatus {
  status: 'not_started' | 'starting' | 'running' | 'failed' | 'stopped';
  error: string | null;
  attempts: number;
  port: number;
}

declare global {
  interface Window {
    electron: IElectronAPI;
  }
}
