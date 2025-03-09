import React, { useState, useMemo } from "react";
import { navigate } from "@reach/router";
import {
  eraseCookie,
  fetchJSON,
  getLocalStorage,
  setLocalStorage,
  getServerUrl,
  getTakinServerUrl
} from "../components/utils";
import { message } from "antd";
import { LoadingIndicator } from "../components/views/atoms";

export interface IUser {
  id: string;
  name: string;
  email?: string;
  image?: string;
  role: string;
  level?: string;
  extraCredits?: number;
  subscriptionCredits?: number;
  subscriptionPurchasedCredits?: number;
}
export interface AppContextType {
  user: IUser | null;
  setUser: any;
  logout: any;
  cookie_name: string;
  darkMode: string;
  setDarkMode: any;
}

const cookie_name =
  process.env.NODE_ENV === "development"
    ? "authjs.session-token"
    : "__Secure-authjs.session-token";

export const appContext = React.createContext<AppContextType>(
  {} as AppContextType
);
const Provider = ({ children }: any) => {
  const serverUrl = getServerUrl();
  const takinServerUrl = getTakinServerUrl();
  const storedValue = getLocalStorage("darkmode", false);
  const [darkMode, setDarkMode] = useState(
    storedValue === null ? "light" : storedValue === "dark" ? "dark" : "light"
  );
  const [user, setUser] = useState<IUser | null>(null);
  const [init, setInit] = useState(false);
  const fetchUser = () => {
    const payLoad = {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    };

    const onSuccess = (data: any) => {
      if (data && !data["status"]) {
        setUser(null);
        setLocalStorage("user_info", null);
        navigate(`${takinServerUrl}/signin`);
        return;
      }
      const userInfo = getLocalStorage("user_info");
      // console.log('获取的用户信息', data.data);
      if (userInfo !== null) {
        setUser(data.data);
        setInit(true);
        return;
      }
      setUser(data.data);
      setLocalStorage("user_info", data.data);
      setInit(true);
    };
    const onError = (err: any) => {
      navigate(`${takinServerUrl}/signin`);
    };
    fetchJSON(`${serverUrl}/users/login`, payLoad, onSuccess, onError);
  };


  const logout = () => {
    const payLoad = {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    };

    const onSuccess = (data: any) => {
      if (data && !data["status"]) return;
      setUser(null);
      setLocalStorage("user_info", null);
      navigate(`${takinServerUrl}/signin`);
    };
    const onError = (err: any) => {
      navigate(`${takinServerUrl}/signin`);
    };
    fetchJSON(`${serverUrl}/users/logout`, payLoad, onSuccess, onError);
  };

  const updateDarkMode = (darkMode: string) => {
    setDarkMode(darkMode);
    setLocalStorage("darkmode", darkMode, false);
  };

  useMemo(() => {
    // 检查浏览器中是否有cookie，如果没有则跳转登录页面；如果有就进行解析
    fetchUser();
  }, []);

  return (
    <appContext.Provider
      value={{
        user,
        setUser,
        logout,
        cookie_name,
        darkMode,
        setDarkMode: updateDarkMode,
      }}
    >
      {init ? (
        children
      ) : (
        <div className="fixed inset-0 w-full h-full flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <LoadingIndicator size={24} />
            <p>loading ..</p>
          </div>
        </div>
      )}
    </appContext.Provider>
  );
};

export default ({ element }: any) => <Provider>{element}</Provider>;
