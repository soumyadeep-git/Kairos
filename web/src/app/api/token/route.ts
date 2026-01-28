import { NextRequest, NextResponse } from "next/server";
import { AccessToken, RoomServiceClient } from "livekit-server-sdk";

export async function GET(request: NextRequest) {
  const roomName = request.nextUrl.searchParams.get("room");
  const participantName = request.nextUrl.searchParams.get("username");

  if (!roomName || !participantName) {
    return NextResponse.json(
      { error: "Missing room or username" },
      { status: 400 }
    );
  }

  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const livekitUrl = process.env.LIVEKIT_URL;

  if (!apiKey || !apiSecret || !livekitUrl) {
    console.error("LiveKit credentials not set");
    return NextResponse.json(
      { error: "Server configuration error" },
      { status: 500 }
    );
  }

  try {
    // Create room with agent dispatch enabled
    const roomService = new RoomServiceClient(livekitUrl, apiKey, apiSecret);
    
    await roomService.createRoom({
      name: roomName,
      emptyTimeout: 60 * 10, // 10 minutes
      maxParticipants: 2,
      metadata: JSON.stringify({ created_by: participantName }),
    });

    // Create token with all required grants
    const at = new AccessToken(apiKey, apiSecret, {
      identity: participantName,
      ttl: "1h",
    });

    at.addGrant({
      roomJoin: true,
      room: roomName,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
      agent: true, // Enable agent dispatch
    });

    const token = await at.toJwt();

    return NextResponse.json({
      token,
      url: livekitUrl,
    });
  } catch (error) {
    console.error("Error creating room/token:", error);
    
    // If room already exists, just create the token
    const at = new AccessToken(apiKey, apiSecret, {
      identity: participantName,
      ttl: "1h",
    });

    at.addGrant({
      roomJoin: true,
      room: roomName,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
      agent: true,
    });

    const token = await at.toJwt();

    return NextResponse.json({
      token,
      url: livekitUrl,
    });
  }
}
