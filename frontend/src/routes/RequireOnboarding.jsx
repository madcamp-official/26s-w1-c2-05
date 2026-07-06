import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { getCurrentUser } from "../api/user";

function RequireOnboarding() {
    const [status, setStatus] = useState("loading"); // "loading" | "onboarded" | "needsOnboarding"

    useEffect(() => {
        let active = true;
        getCurrentUser().then(({ current_learning_id }) => {
            if (!active) return;
            setStatus(current_learning_id ? "onboarded" : "needsOnboarding");
        });
        return () => {
            active = false;
        };
    }, []);

    if (status === "loading") return null;
    if (status === "needsOnboarding") return <Navigate to="/onboarding" replace />;
    return <Outlet />;
}

export default RequireOnboarding;
