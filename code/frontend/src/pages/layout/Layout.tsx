import { Outlet, Link } from "react-router-dom";
import styles from "./Layout.module.css";
import TFLogo from "../../assets/TFLogo.png";
import { CopyRegular } from "@fluentui/react-icons";
import { Dialog, Stack, TextField } from "@fluentui/react";
import { useEffect, useState } from "react";

const Layout = () => {
    const [copyClicked, setCopyClicked] = useState<boolean>(false);
    const [copyText, setCopyText] = useState<string>("Copy URL");

    const handleCopyClick = () => {
        navigator.clipboard.writeText(window.location.href);
        setCopyClicked(true);
    };

    useEffect(() => {
        if (copyClicked) {
            setCopyText("Copied URL");
        }
    }, [copyClicked]);

    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Stack horizontal verticalAlign="center">
                        <img
                            src={TFLogo}
                            className={styles.headerIcon}
                            aria-hidden="true"
                        />
                        <Link to="/" className={styles.headerTitleContainer}>
                            <h3 className={styles.headerTitle}>TechFabric AI</h3>
                        </Link>
                    </Stack>
                </div>
            </header>
            <Outlet />
            <Stack horizontal verticalAlign="center" style={{ gap: "8px" }}>
                <TextField className={styles.urlTextBox} defaultValue={window.location.href} readOnly />
                <div
                    className={styles.copyButtonContainer}
                    role="button"
                    tabIndex={0}
                    aria-label="Copy"
                    onClick={handleCopyClick}
                    onKeyDown={e => e.key === "Enter" || e.key === " " ? handleCopyClick() : null}
                >
                    <CopyRegular className={styles.copyButton} />
                    <span className={styles.copyButtonText}>{copyText}</span>
                </div>
            </Stack>
        </div >
    );
};

export default Layout;
