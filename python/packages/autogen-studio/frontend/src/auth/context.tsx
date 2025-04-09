import React, { createContext, useState, useEffect, useContext } from "react";
import { authAPI, User } from "./api";
import { message } from "antd";
import { navigate } from "gatsby";
import {
  sanitizeUrl,
  sanitizeRedirectUrl,
  isValidMessageOrigin,
  isValidUserObject,
} from "../components/utils/security-utils";

import {
  getCookie,
  getTakinServerUrl
} from "../components/utils/utils";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authType: string;
  login: () => Promise<string>;
  logout: () => void;
  // handleAuthCallback: (code: string, state?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);


export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
 
  const handleLogin = async () => {
    const userData = await authAPI.getCurrentUser();
    setUser(userData);
  };
  // Load user on initial render if token exists
  useEffect(() => {
    const loadUser = async () => {
      try {
        await handleLogin();
      } catch (error) {
        console.error("Failed to load user:", error);
        // removeToken(); // Clear invalid token
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  // Login function - gets login URL but doesn't redirect
  // (redirection is handled in the login component with popup)
  const login = async (): Promise<string> => {
    try {
      await handleLogin();
      return "";
    } catch (error) {
      message.error("Failed to initiate login");
      console.error("Login error:", error);
      return "";
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    const takinServerUrl = getTakinServerUrl();
    try {
      // Call logout API endpoint
      await authAPI.logout();
      // Clear user state
      setUser(null);
      // Redirect to login
      navigate(`${takinServerUrl}/signin`);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    authType: "takin",
    login,
    logout,

  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook to use auth context
export const useAuth = (): AuthContextType => {
  if (typeof window === "undefined") {
    // Return default values or empty implementation
    return {
      user: null,
      isAuthenticated: false,
      isLoading: true,
      authType: "takin",
      cookie_name: "",
      login: async () => "",
      logout: () => { },
      // handleAuthCallback: async () => {},
    } as AuthContextType;
  }
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
