export type SocialPlatform =
  | "YouTube" | "Discord" | "Instagram" | "X" | "TikTok" | "Telegram"
  | "Spotify" | "SoundCloud" | "GitHub" | "Reddit" | "Twitch" | "Snapchat"
  | "Facebook" | "LinkedIn" | "Steam" | "Roblox" | "PayPal" | "Pinterest"
  | "Threads" | "Kick"
  | "Patreon" | "Bitcoin" | "Ethereum" | "Litecoin" | "Solana" | "Email" | "Custom URL";

export type BadgeName = "Verified" | "Premium" | "Staff" | "Helper" | "Donor" | "Gifter" | "OG" | "Server Booster" | "Bug Hunter" | "Winner" | "Second Place" | "Third Place";
export type BackgroundEffect = "None" | "Particles" | "Stars" | "Glow";
export type UsernameEffect = "None" | "Glow" | "Gradient" | "Shimmer";

export interface ProfileAsset {
  url: string | null;
  name?: string;
  type?: string;
}

export interface SocialLink {
  id: string;
  platform: SocialPlatform;
  label: string;
  value: string;
  enabled: boolean;
  displayMode: "link" | "text";
  clicks: number;
}

export interface ProfileBadge {
  id: string;
  name: BadgeName;
  description: string;
  owned: boolean;
  enabled: boolean;
  color: string;
}

export interface ProfileConfig {
  profile: {
    username: string;
    displayName: string;
    description: string;
    location: string;
    views: number;
    uid: string;
  };
  settings: {
    accentColor: string;
    textColor: string;
    backgroundColor: string;
    iconColor: string;
    profileOpacity: number;
    backgroundOpacity: number;
    profileBlur: number;
    profileRadius: number;
    profileGradient: boolean;
    showViews: boolean;
    showBadges: boolean;
    showSocials: boolean;
    entryScreen: boolean;
    entryText: string;
    backgroundEffect: BackgroundEffect;
    usernameEffect: UsernameEffect;
    usernameGlow: boolean;
    socialGlow: boolean;
    badgeGlow: boolean;
  };
  assets: {
    avatar: ProfileAsset;
    background: ProfileAsset;
    backgroundVideo: ProfileAsset;
    audio: ProfileAsset;
    cursor: ProfileAsset;
    audioEnabled: boolean;
    volume: number;
  };
  socials: SocialLink[];
  badges: ProfileBadge[];
}
