import React, { useState } from "react";
import { AuthProvider, useAuth } from "../auth/context";
import { getLocalStorage, setLocalStorage } from "../components/utils/utils";
import { User } from "../auth/api";

export interface AppContextType {
  darkMode: string;
  setDarkMode: any;
  user: User | null;
  setUser: any;
  logout: any;
  cookie_name: string;
}

export const appContext = React.createContext<AppContextType>(
  {} as AppContextType
);

const cookie_name =
  process.env.NODE_ENV === "development"
    ? "authjs.session-token"
    : "__Secure-authjs.session-token";

const AppProvider = ({ children }: any) => {
  // Dark mode handling
  const storedValue = getLocalStorage("darkmode", false);
  const [darkMode, setDarkMode] = useState(
    storedValue === null ? "light" : storedValue === "dark" ? "dark" : "light"
  );

  const updateDarkMode = (darkMode: string) => {
    setDarkMode(darkMode);
    setLocalStorage("darkmode", darkMode, false);
  };

  // We'll use auth context to get user and logout function
  const { user, logout } = useAuth();

  return (
    <appContext.Provider
      value={{
        user,
        setUser: () => {},
        logout,
        cookie_name,
        darkMode,
        setDarkMode: updateDarkMode,
      }}
    >
      {children}
    </appContext.Provider>
  );
};

// Combined provider that includes both Auth and App context
export default ({ element }: any) => (
  <AuthProvider>
    <AppProvider>{element}</AppProvider>
  </AuthProvider>
);