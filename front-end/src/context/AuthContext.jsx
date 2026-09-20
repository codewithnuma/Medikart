import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

import axiosInstance, {
  markLoggedOut,
  resetLogoutState,
} from "../axiosInstance";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const hasFetchedUser = useRef(false);

  const fetchUser = async () => {
    try {
      const response = await axiosInstance.get(
        "/accounts/me/"
      );

      const rawRole =
        response.data?.role || "";

      const normalizedUser = {
        ...response.data,
        role: String(rawRole)
          .trim()
          .toLowerCase(),
      };

      setUser(normalizedUser);

      return normalizedUser;
    } catch {
      setUser(null);

      return null;
    } finally {
      setLoading(false);
      hasFetchedUser.current = true;
    }
  };

  useEffect(() => {
    if (!hasFetchedUser.current) {
      fetchUser();
    }
  }, []);

  const login = async (
    email,
    password
  ) => {
    try {
      resetLogoutState();

      const response =
        await axiosInstance.post(
          "/accounts/login/",
          {
            email,
            password,
          }
        );

      const loggedInUser =
        await fetchUser();

      if (!loggedInUser) {
        return {
          success: false,
          error:
            "Login succeeded, but user information could not be loaded.",
        };
      }

      return {
        success: true,
        user: loggedInUser,
        data: response.data,
      };
    } catch (error) {
      const data =
        error.response?.data;

      return {
        success: false,
        error:
          data?.detail ||
          data?.message ||
          data?.non_field_errors?.[0] ||
          "Login failed.",
      };
    }
  };

  const logout = async () => {
    try {
      await axiosInstance.post(
        "/accounts/logout/"
      );
    } catch (error) {
      console.error(
        "Logout error:",
        error
      );
    } finally {
      markLoggedOut();

      setUser(null);

      hasFetchedUser.current = true;

      window.location.href = "/login";
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
        fetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
};