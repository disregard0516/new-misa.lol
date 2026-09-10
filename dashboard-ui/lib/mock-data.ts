import type { ProfileConfig, ProfileBadge, SocialLink } from "./types";

export const mockSocials: SocialLink[] = [
  { id: "discord", platform: "Discord", label: "Discord", value: "demo", enabled: true, displayMode: "text", clicks: 0 },
  { id: "instagram", platform: "Instagram", label: "Instagram", value: "@demo", enabled: true, displayMode: "link", clicks: 0 },
  { id: "youtube", platform: "YouTube", label: "YouTube", value: "@demo", enabled: true, displayMode: "link", clicks: 0 },
  { id: "telegram", platform: "Telegram", label: "Telegram", value: "t.me/demo", enabled: true, displayMode: "link", clicks: 0 },
  { id: "github", platform: "GitHub", label: "GitHub", value: "github.com/demo", enabled: true, displayMode: "link", clicks: 0 },
];

const badgeInfo: Array<[ProfileBadge["name"], string, string]> = [
  ["Verified", "Verified creator", "#8f8dff"],
  ["Premium", "Premium member", "#d9a4ff"],
  ["Staff", "Misa.lol staff", "#ff9fcf"],
  ["Helper", "Community helper", "#76d9c8"],
  ["Donor", "Generous supporter", "#ffcb71"],
  ["Gifter", "Community gifter", "#ff8f9d"],
  ["OG", "Original member", "#98adff"],
  ["Server Booster", "Server booster", "#f69bd7"],
  ["Bug Hunter", "Bug hunter", "#bbd968"],
  ["Winner", "Event winner", "#ffcf76"],
  ["Second Place", "Second place", "#bbc6d8"],
  ["Third Place", "Third place", "#c69470"],
];

export const mockBadges: ProfileBadge[] = badgeInfo.map(([name, description, color], index) => ({
  id: name.toLowerCase().replaceAll(" ", "-"), name, description,
  owned: [0, 1, 6].includes(index), enabled: [0, 1, 6].includes(index), color,
}));

export const mockProfile: ProfileConfig = {
  profile: { username: "demo", displayName: "Demo User", description: "A little corner of the internet.", location: "", views: 0, uid: "1000001" },
  settings: {
    accentColor: "#9b87f5", textColor: "#ffffff", backgroundColor: "#08080d", iconColor: "#d8d3ff",
    profileOpacity: 10, backgroundOpacity: 88, profileBlur: 24, profileRadius: 24, profileGradient: true, showViews: true, showBadges: true, showSocials: true,
    entryScreen: true, entryText: "click to enter...", backgroundEffect: "Glow", usernameEffect: "Glow",
    usernameGlow: true, socialGlow: true, badgeGlow: true,
  },
  assets: { avatar: { url: null }, background: { url: null }, backgroundVideo: { url: null }, audio: { url: null }, cursor: { url: null }, audioEnabled: true, volume: 65 },
  socials: mockSocials,
  badges: mockBadges,
};

export const cloneMockProfile = (): ProfileConfig => structuredClone(mockProfile);

export const platformOptions: ProfileConfig["socials"][number]["platform"][] = [
  "YouTube", "Discord", "Instagram", "X", "TikTok", "Telegram", "Spotify", "SoundCloud", "GitHub", "Reddit", "Twitch", "Snapchat", "Facebook", "LinkedIn", "Steam", "Roblox", "PayPal", "Pinterest", "Patreon", "Threads", "Kick", "Bitcoin", "Ethereum", "Litecoin", "Solana", "Email", "Custom URL",
];
