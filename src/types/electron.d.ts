export interface IElectronAPI {
  openFile: () => Promise<string | null>;
  readFile: (filePath: string) => Promise<string>;
  saveFile: (data: any) => Promise<string | null>;
  getAppVersion: () => Promise<string>;
}

declare global {
  interface Window {
    electron: IElectronAPI;
  }
}
